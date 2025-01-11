import sqlite3
from datetime import datetime
from typing import Optional

from .document import DocumentType, DocumentMetadata


class MetadataStore:
    def __init__(self, db_path: str):
        """
        Initialize the metadata store

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_metadata (
                    doc_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    modified_at INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    additional_metadata TEXT
                )
            """)

    def _convert_to_metadata(self, row: sqlite3.Row) -> DocumentMetadata:
        """Convert a database row to DocumentMetadata"""
        additional_metadata = None
        if row["additional_metadata"]:
            import json

            additional_metadata = json.loads(row["additional_metadata"])

        return DocumentMetadata(
            doc_id=row["doc_id"],
            name=row["name"],
            doc_type=DocumentType(row["doc_type"]),
            created_at=datetime.fromtimestamp(row["created_at"]),
            modified_at=datetime.fromtimestamp(row["modified_at"]),
            source=row["source"],
            size=row["size"],
            additional_metadata=additional_metadata,
        )

    def get_metadata(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Get metadata for a document by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM document_metadata WHERE doc_id = ?", (doc_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._convert_to_metadata(row)
        return None

    def update_metadata(self, metadata: DocumentMetadata):
        """Insert or update metadata for a document"""
        with sqlite3.connect(self.db_path) as conn:
            additional_metadata = None
            if metadata.additional_metadata:
                import json

                additional_metadata = json.dumps(metadata.additional_metadata)

            conn.execute(
                """
                INSERT OR REPLACE INTO document_metadata 
                (doc_id, name, doc_type, created_at, modified_at, source, size, additional_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metadata.doc_id,
                    metadata.name,
                    metadata.doc_type.value,
                    int(metadata.created_at.timestamp()),
                    int(metadata.modified_at.timestamp()),
                    metadata.source,
                    metadata.size,
                    additional_metadata,
                ),
            )

    def remove_metadata(self, doc_id: str):
        """Remove metadata for a document"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM document_metadata WHERE doc_id = ?", (doc_id,))

    def list_metadata(self) -> list[DocumentMetadata]:
        """List all document metadata"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM document_metadata")
            return [self._convert_to_metadata(row) for row in cursor.fetchall()]
