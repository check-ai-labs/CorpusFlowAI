import os
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from watchdog.observers import Observer

from .base import DocumentSource
from .document import DocumentType, DocumentMetadata, Document
from .exceptions import DocumentSourceException
from .metadata_store import MetadataStore


class LocalFileSystemSource(DocumentSource):
    def __init__(self, root_path: str, db_path: Optional[str] = None):
        """
        Initialize local filesystem document source

        Args:
            root_path: Root directory to monitor
            db_path: Optional path to SQLite database file. If not provided,
                     will create 'metadata.db' in the root_path, if passed in user must manage its lifecycle 
                     if left blank it will be recreated each load to make sure we are not mssing any files
        """
        self.root_path = os.path.abspath(root_path)
        if not db_path:
            db_path = "./metadata_local.db"
            if os.path.exists(db_path):
                os.remove(db_path)

        self.metadata_store = MetadataStore(db_path)
        self._observer: Optional[Observer] = None
        self._watch_thread: Optional[threading.Thread] = None
        self._running = False

    def _get_metadata(self, file_path: str) -> Optional[DocumentMetadata]:
        """Generate metadata for a file"""
        try:
            ext = os.path.splitext(file_path)[1].lower()[1:]
            try:
                doc_type = DocumentType(ext)
            except ValueError:
                return None

            stats = os.stat(file_path)
            return DocumentMetadata(
                doc_id=file_path,
                name=os.path.basename(file_path),
                doc_type=doc_type,
                created_at=datetime.fromtimestamp(stats.st_ctime),
                modified_at=datetime.fromtimestamp(stats.st_mtime),
                source="local",
                size=stats.st_size,
            )
        except (OSError, IOError):
            return None

    def connect(self, credentials: Dict[str, Any] = None) -> bool:
        """Verify root path exists and initialize metadata cache"""
        if not os.path.exists(self.root_path):
            return False

        # Initial scan to populate metadata cache
        for root, _, files in os.walk(self.root_path):
            for file in files:
                file_path = os.path.join(root, file)
                metadata = self._get_metadata(file_path)
                if metadata:
                    self.metadata_store.update_metadata(metadata)

        return True

    def disconnect(self) -> bool:
        return True

    def watch_documents(
        self,
        callback: Callable[[str, DocumentMetadata], None],
        interval: Optional[int] = None,
    ) -> bool:
        """Start watching for document changes"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            raise ImportError(
                "watchdog is required for watching - pip install watchdog"
            )

        class DocHandler(FileSystemEventHandler):
            def __init__(self, source, callback):
                self.source = source
                self.callback = callback

            def on_created(self, event):
                if not event.is_directory:
                    try:
                        metadata = self.source._get_metadata(event.src_path)
                        if metadata:
                            self.source.metadata_store.update_metadata(metadata)
                            self.callback("created", metadata)
                    except Exception:
                        pass

            def on_modified(self, event):
                if not event.is_directory:
                    try:
                        # Try to get new metadata
                        new_metadata = self.source._get_metadata(event.src_path)
                        if new_metadata:
                            self.source.metadata_store.update_metadata(new_metadata)
                            self.callback("modified", new_metadata)
                        else:
                            # Fall back to cached metadata
                            cached_metadata = self.source.metadata_store.get_metadata(
                                event.src_path
                            )
                            if cached_metadata:
                                self.callback("modified", cached_metadata)
                    except Exception:
                        pass

            def on_deleted(self, event):
                if not event.is_directory:
                    try:
                        # Get cached metadata before removing
                        metadata = self.source.metadata_store.get_metadata(
                            event.src_path
                        )
                        if metadata:
                            self.callback("deleted", metadata)
                            self.source.metadata_store.remove_metadata(event.src_path)
                    except Exception:
                        pass

        self._observer = Observer()
        self._observer.schedule(
            DocHandler(self, callback), self.root_path, recursive=True
        )
        self._observer.start()
        return True

    def stop_watching(self) -> bool:
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        return True

    def list_documents(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentMetadata]:
        """List all documents using cached metadata"""
        return self.metadata_store.list_metadata()

    def get_document(self, doc_id: str) -> Document:
        """Get document content and metadata"""
        content = ""
        if os.path.exists(doc_id):
            with open(doc_id, "rb") as f:
                content = f.read()

        metadata = self.metadata_store.get_metadata(doc_id)
        if not metadata:
            # Generate fresh metadata if not in cache
            metadata = self._get_metadata(doc_id)
            if not metadata:
                print(f"Invalid document type: {doc_id}")
                raise DocumentSourceException(f"Invalid document type: {doc_id}")
            self.metadata_store.update_metadata(metadata)

        return Document(metadata, content)

    def search_documents(self, query: str) -> List[DocumentMetadata]:
        """Search documents using cached metadata"""
        all_docs = self.metadata_store.list_metadata()
        return [doc for doc in all_docs if query.lower() in doc.name.lower()]
