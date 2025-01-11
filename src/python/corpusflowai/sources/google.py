import os
import time
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

from .base import DocumentSource
from .document import DocumentType, DocumentMetadata, Document
from .exceptions import DocumentSourceException
from .metadata_store import MetadataStore

SCOPES = ['https://www.googleapis.com/auth/drive.readonly',
          'https://www.googleapis.com/auth/drive.activity.readonly']



class GoogleDocsSource(DocumentSource):
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Google Docs document source

        Args:
            cache_dir: Directory to store SQLite database and document cache
        """
        if not db_path:
            db_path = "./metadata_gdocs.db"
            if os.path.exists(db_path):
                os.remove(db_path)

        self.metadata_store = MetadataStore(db_path)

        self.service = None
        self._watch_thread: Optional[threading.Thread] = None
        self._running = False

    def _convert_gdoc_to_metadata(self, gdoc: Dict[str, Any]) -> DocumentMetadata:
        """Convert Google Doc metadata to DocumentMetadata"""
        # Map common MIME types to our DocumentType
        mime_type_map = {
            "application/vnd.google-apps.document": DocumentType.DOCX,
            "application/pdf": DocumentType.PDF,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.DOCX,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": DocumentType.XLSX,
            "application/vnd.google-apps.spreadsheet": DocumentType.XLSX,
            "text/plain": DocumentType.TXT,
            "application/vnd.google.colaboratory": DocumentType.TXT,
            "application/vnd.google-apps.presentation": DocumentType.PPTX,
        }

        mime_type = gdoc.get("mimeType", "")
        try:
            doc_type = mime_type_map[mime_type]
        except KeyError:
            # print(f"Missing map {mime_type}")
            # Default to GDOC for Google Docs native files
            doc_type = DocumentType.GDOC if "google-apps" in mime_type else None
            if not doc_type:
                raise ValueError(f"Unsupported MIME type: {mime_type}")

        # Convert timestamps
        created_time = datetime.fromisoformat(
            gdoc["createdTime"].replace("Z", "+00:00")
        )
        modified_time = datetime.fromisoformat(
            gdoc["modifiedTime"].replace("Z", "+00:00")
        )

        return DocumentMetadata(
            doc_id=gdoc["id"],
            name=gdoc["name"],
            doc_type=doc_type,
            created_at=created_time,
            modified_at=modified_time,
            source="gdocs",
            size=int(gdoc.get("size", 0)),
            additional_metadata={
                "owners": [owner["emailAddress"] for owner in gdoc.get("owners", [])],
                "shared": gdoc.get("shared", False),
                "starred": gdoc.get("starred", False),
                "mime_type": mime_type,
            },
        )

    def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to Google Docs API

        Args:
            credentials: Dictionary containing Google OAuth2 credentials
        """
        try:
            try:
                import os.path

                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials
                from google_auth_oauthlib.flow import InstalledAppFlow
                from googleapiclient.discovery import build
                from googleapiclient.errors import HttpError

            except ImportError as missing:
                raise ImportError(
                    "google tools not available - pip install corpusflowai[google]"
                ) from missing

            creds = None
            creds_file = credentials['credentials.json']
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)

            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

            try:
                self.service = build("drive", "v3", credentials=creds)
                # Initial sync to populate metadata cache
                self._sync_metadata()

            except HttpError as error:
                print('An error occurred: %s' % error)
                return False
            
            return True
        except Exception as e:
            raise DocumentSourceException(f"Failed to connect to Google Docs: {str(e)}")

    def disconnect(self) -> bool:
        """Disconnect from Google Docs API"""
        if self.service:
            self.service = None
        return True

    def _sync_metadata(self):
        """Sync all document metadata to local cache"""
        if not self.service:
            raise DocumentSourceException("Not connected to Google Docs")

        try:
            # List all files, getting required metadata
            page_token = None
            while True:
                results = (
                    self.service.files()
                    .list(
                        pageSize=100,
                        fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, size, owners, shared, starred)",
                        pageToken=page_token,
                    )
                    .execute()
                )

                for item in results.get("files", []):
                    try:
                        metadata = self._convert_gdoc_to_metadata(item)
                        self.metadata_store.update_metadata(metadata)
                    except ValueError:
                        # Skip unsupported document types
                        continue

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

        except Exception as e:
            raise DocumentSourceException(f"Failed to sync metadata: {str(e)}")

    def list_documents(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentMetadata]:
        """List all documents using cached metadata"""
        return self.metadata_store.list_metadata()

    def get_document(self, doc_id: str) -> Document:
        """
        Get document content and metadata

        For Google Docs native files, exports as PDF
        For other files, downloads in original format
        """
        if not self.service:
            raise DocumentSourceException("Not connected to Google Docs")

        try:
            metadata = self.metadata_store.get_metadata(doc_id)
            if not metadata:
                raise DocumentSourceException(f"Document not found: {doc_id}")

            mime_type = metadata.additional_metadata.get("mime_type", "")

            # https://developers.google.com/drive/api/guides/ref-export-formats
            if "google-apps" in mime_type:
                d_mime_type = "application/pdf"
                if "spreadsheet" in mime_type:
                    d_mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                elif "document" in mime_type:
                    d_mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif "presentation" in mime_type:
                    d_mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                
                response = (
                    self.service.files()
                    .export(fileId=doc_id, mimeType=d_mime_type)
                    .execute()
                )
            else:
                # Download other files in original format
                response = self.service.files().get_media(fileId=doc_id).execute()
            
            return Document(metadata, response)

        except Exception as e:
            raise DocumentSourceException(f"Failed to get document: {str(e)}")

    def search_documents(self, query: str) -> List[DocumentMetadata]:
        """Search documents using Google Drive API"""
        if not self.service:
            raise DocumentSourceException("Not connected to Google Docs")

        try:
            results = (
                self.service.files()
                .list(
                    q=f"name contains '{query}'",
                    fields="files(id, name, mimeType, createdTime, modifiedTime, size, owners, shared, starred)",
                )
                .execute()
            )

            documents = []
            for item in results.get("files", []):
                try:
                    metadata = self._convert_gdoc_to_metadata(item)
                    # Update cache with latest metadata
                    self.metadata_store.update_metadata(metadata)
                    documents.append(metadata)
                except ValueError:
                    continue

            return documents

        except Exception as e:
            raise DocumentSourceException(f"Failed to search documents: {str(e)}")

    def watch_documents(
        self,
        callback: Callable[[str, DocumentMetadata], None],
        interval = 60,
    ) -> bool:
        """
        Watch for document changes using periodic polling

        Args:
            callback: Function to call when changes are detected
            interval: Polling interval in seconds (default: 60)
        """
        if not self.service:
            raise DocumentSourceException("Not connected to Google Docs")

        if self._watch_thread and self._running:
            return True  # Already watching

        self._running = True
        def watch_loop():
            # Track last check time
            last_check = datetime.utcnow().isoformat() + "Z"

            while self._running:
                try:
                    # Query for changes since last check
                    print(f"Query for changes since last check {last_check}")
                    results = (
                        self.service.files()
                        .list(
                            q=f"modifiedTime > '{last_check}'",
                            fields="files(id, name, mimeType, createdTime, modifiedTime, size, owners, shared, starred, trashed)",
                        )
                        .execute()
                    )

                    this_check = datetime.utcnow().isoformat() + "Z"

                    for item in results.get("files", []):
                        try:
                            doc_id = item["id"]
                            old_metadata = self.metadata_store.get_metadata(doc_id)

                            if item.get("trashed", False):
                                if old_metadata:
                                    callback("deleted", old_metadata)
                                    self.metadata_store.remove_metadata(doc_id)
                            else:
                                new_metadata = self._convert_gdoc_to_metadata(item)
                                if not old_metadata:
                                    self.metadata_store.update_metadata(new_metadata)
                                    callback("created", new_metadata)
                                else:
                                    self.metadata_store.update_metadata(new_metadata)
                                    callback("modified", new_metadata)

                        except ValueError:
                            continue

                    last_check = this_check

                except Exception as e:
                    print(f"Error in Google Docs watch loop: {str(e)}")
                    raise e

                time.sleep(interval)

        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()
        return True

    def stop_watching(self) -> bool:
        """Stop watching for document changes"""
        self._running = False
        if self._watch_thread:
            self._watch_thread.join(timeout=1)
            self._watch_thread = None
        return True
