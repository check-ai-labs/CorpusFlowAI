from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable

from .document import DocumentMetadata, Document

class DocumentSource(ABC):
    @abstractmethod
    def connect(self, credentials: Dict[str, Any]) -> bool:
        """Establish connection to the document source"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection to the document source"""
        pass
    
    @abstractmethod
    def list_documents(self, filters: Optional[Dict[str, Any]] = None) -> List[DocumentMetadata]:
        """List available documents with optional filtering"""
        pass
    
    @abstractmethod
    def get_document(self, doc_id: str) -> Document:
        """Retrieve a specific document by ID"""
        pass
    
    @abstractmethod
    def search_documents(self, query: str) -> List[DocumentMetadata]:
        """Search for documents using a query string"""
        pass

    @abstractmethod
    def watch_documents(self, callback: Callable[[str, DocumentMetadata], None], 
                       interval: Optional[int] = None) -> bool:
        """
        Watch for document changes and call the callback when changes are detected
        
        Args:
            callback: Function to call when a document changes. Takes action type 
                     ('created', 'modified', 'deleted') and DocumentMetadata
            interval: Optional polling interval in seconds for sources that don't 
                     support native watching
                     
        Returns:
            bool: True if watching was successfully started
        """
        pass
    
    @abstractmethod    
    def stop_watching(self) -> bool:
        """
        Stop watching for document changes
        
        Returns:
            bool: True if watching was successfully stopped
        """
        pass
