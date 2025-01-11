import time
from corpusflowai.manager.base import DocumentManager
from corpusflowai.sources import (
    LocalFileSystemSource,
    DocumentMetadata,
    # GoogleDocsSource,
    # Office365Source,
    # S3Source
)


def process_document(doc):
    print(f"Processing changed document {doc.metadata.name}")

def delete_document(doc):
    print(f"Delete document {doc.metadata.name}")

# Example usage:
def main():
    def handle_change(source: str, action: str, metadata: DocumentMetadata):
        print(f"{action.title()} in {source}: {metadata.name}")
        if action == "modified":
            print("Handling modified")
            doc = doc_manager.get_document(source, metadata.doc_id)
            process_document(doc)
        elif action == "created":
            print("Handling created")
            doc = doc_manager.get_document(source, metadata.doc_id)
            delete_document(doc)
            process_document(doc)
        elif action == "deleted":
            print("Handling deleted")
            doc = doc_manager.get_document(source, metadata.doc_id)
            delete_document(doc)

    # Create document manager
    doc_manager = DocumentManager()

    # Add local file system source
    local_source = LocalFileSystemSource(root_path="./test_docs")

    doc_manager.add_source("local", local_source)

    # Connect to sources
    doc_manager.connect_source("local", {})

    # List all documents
    all_docs = doc_manager.list_all_documents()
    for source_name, docs in all_docs.items():
        print(f"\nDocuments from {source_name}:")
        for doc in docs:
            print(f"- {doc.name} ({doc.doc_type.value})")
            # Process all of the files that you currently have first

    doc_manager.add_watch_callback("processor", handle_change)
    doc_manager.watch_all_sources(
        {
            "local": None,  # Use native events
        }
    )

    try:
        # Keep program running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        doc_manager.stop_watching_all()


if __name__ == "__main__":
    main()
