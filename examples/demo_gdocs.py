import time
import uuid
from corpusflowai.manager.base import DocumentManager
from corpusflowai.sources import (
    DocumentMetadata,
    GoogleDocsSource,
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
            with open(f"{str(uuid.uuid4())}.{doc.metadata.doc_type.value}", 'wb') as f:
                f.write(doc.content)
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
    gdocs = GoogleDocsSource()

    doc_manager.add_source("gdocs", gdocs)

    # Connect to sources
    # Get your creds from https://console.cloud.google.com/apis/
    if doc_manager.connect_source("gdocs", {
            "credentials.json": "./gdocs_credentials.json"
        }):


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
                "gdocs": 60, # 1 minute polling
            }
        )

        try:
            # Keep program running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            doc_manager.stop_watching_all()
    else:
        print("Unable to connect to the drive")


if __name__ == "__main__":
    main()
