from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

class DocumentType(Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    TXT = "txt"
    GDOC = "gdoc"
    PPTX = "pptx"
    
class DocumentMetadata:
    def __init__(
        self,
        doc_id: str,
        name: str,
        doc_type: DocumentType,
        created_at: datetime,
        modified_at: datetime,
        source: str,
        size: int,
        additional_metadata: Optional[Dict[str, Any]] = None
    ):
        self.doc_id = doc_id
        self.name = name
        self.doc_type = doc_type
        self.created_at = created_at
        self.modified_at = modified_at
        self.source = source
        self.size = size
        self.additional_metadata = additional_metadata or {}

class Document:
    def __init__(self, metadata: DocumentMetadata, content: Any):
        self.metadata = metadata
        self.content = content
