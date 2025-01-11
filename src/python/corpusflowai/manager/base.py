from typing import List, Dict, Any, Optional, Callable

from ..sources.base import DocumentSource
from ..sources.document import DocumentMetadata, Document
from ..sources.exceptions import DocumentSourceException


class DocumentManager:
    def __init__(self):
        self.sources: Dict[str, DocumentSource] = {}
        self.watch_callbacks: Dict[str, Callable[[str, str, DocumentMetadata], None]] = {}

    def add_source(self, name: str, source: DocumentSource):
        self.sources[name] = source
    
    def remove_source(self, name: str):
        if name in self.sources:
            self.sources[name].disconnect()
            del self.sources[name]
    
    def connect_source(self, name: str, credentials: Dict[str, Any]) -> bool:
        if name not in self.sources:
            raise DocumentSourceException(f"Source not found: {name}")
        return self.sources[name].connect(credentials)
    
    def list_all_documents(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[DocumentMetadata]]:
        results = {}
        for source_name, source in self.sources.items():
            try:
                results[source_name] = source.list_documents(filters)
            except DocumentSourceException as e:
                print(f"Error listing documents from {source_name}: {str(e)}")
                results[source_name] = []
        return results
    
    def search_all_documents(self, query: str) -> Dict[str, List[DocumentMetadata]]:
        results = {}
        for source_name, source in self.sources.items():
            try:
                results[source_name] = source.search_documents(query)
            except DocumentSourceException as e:
                print(f"Error searching documents from {source_name}: {str(e)}")
                results[source_name] = []
        return results
    
    def get_document(self, source_name: str, doc_id: str) -> Document:
        if source_name not in self.sources:
            raise DocumentSourceException(f"Source not found: {source_name}")
        return self.sources[source_name].get_document(doc_id)

    def add_watch_callback(self, name: str, 
                          callback: Callable[[str, str, DocumentMetadata], None]):
        """
        Add a callback to be called when documents change in any source
        
        Args:
            name: Unique name for this callback
            callback: Function taking source name, action type, and DocumentMetadata
        """
        self.watch_callbacks[name] = callback
        
    def remove_watch_callback(self, name: str):
        """Remove a previously registered callback"""
        if name in self.watch_callbacks:
            del self.watch_callbacks[name]
    
    def watch_all_sources(self, interval: Optional[dict] = None) -> bool:
        """
        Start watching all sources for changes
        
        Args:
            interval: Optional polling interval in seconds
            
        Returns:
            bool: True if watching was successfully started for all sources
        """
        success = True
        for source_name, source in self.sources.items():
            try:
                def make_callback(src_name):
                    def callback(action: str, metadata: DocumentMetadata):
                        for cb in self.watch_callbacks.values():
                            cb(src_name, action, metadata)
                    return callback
                
                source.watch_documents(make_callback(source_name), interval[source_name])
            except Exception as e:
                print(f"DocumentManager: Error setting up watch for {source_name}: {str(e)}")
                success = False
                raise e
        return success
    
    def stop_watching_all(self) -> bool:
        """
        Stop watching all sources
        
        Returns:
            bool: True if watching was successfully stopped for all sources
        """
        success = True
        for source_name, source in self.sources.items():
            try:
                source.stop_watching()
            except Exception as e:
                print(f"Error stopping watch for {source_name}: {str(e)}")
                success = False
        return success
