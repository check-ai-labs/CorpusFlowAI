# CorpusFlow

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

CorpusFlow is a robust Python framework designed to streamline the process of gathering training data for Large Language Models. It provides a unified interface to harvest documents from multiple sources while maintaining provenance and metadata, making it an essential tool for ML teams building training pipelines.

## 🚀 Key Features

- **Universal Document Access**: Seamlessly connect to multiple document sources:
  - Google Workspace (Docs, Sheets, Drive)
  - Microsoft Office 365
  - Amazon S3
  - Local File Systems
  - *Easily extensible for additional sources*

- **Smart Document Processing**:
  - Automatic document type detection
  - Rich metadata extraction and preservation
  - Configurable filtering and search capabilities
  - Bulk processing with progress tracking

- **Built for ML Pipelines**:
  - Structured output format for training data
  - Document provenance tracking
  - Configurable preprocessing hooks
  - Batching and streaming support

- **Enterprise Ready**:
  - Comprehensive error handling
  - Detailed logging and monitoring
  - Rate limiting and throttling
  - Authentication management
  - Async operations support

## 🔧 Installation

```bash
pip install corpusflow
```

For development installation:

```bash
git clone https://github.com/yourusername/corpusflow.git
cd corpusflow
pip install -e ".[dev]"
```

## 🚦 Quick Start

```python
from corpusflow import DocumentManager
from corpusflow.sources import LocalFileSystemSource, GoogleDocsSource

# Initialize the document manager
doc_manager = DocumentManager()

# Add document sources
local_source = LocalFileSystemSource("/path/to/documents")
gdocs_source = GoogleDocsSource()

doc_manager.add_source("local", local_source)
doc_manager.add_source("gdocs", gdocs_source)

# Connect to sources
doc_manager.connect_source("local", {})
doc_manager.connect_source("gdocs", {
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "refresh_token": "your-refresh-token"
})

# List all documents
all_docs = doc_manager.list_all_documents()

# Search across all sources
results = doc_manager.search_all_documents("machine learning")
```

## 📚 Documentation

### Adding a New Document Source

Extend the `DocumentSource` base class to add support for new document sources:

```python
from corpusflow import DocumentSource, Document, DocumentMetadata

class CustomSource(DocumentSource):
    def connect(self, credentials):
        # Implement connection logic
        pass
    
    def list_documents(self, filters=None):
        # Implement document listing
        pass
    
    def get_document(self, doc_id):
        # Implement document retrieval
        pass
    
    def search_documents(self, query):
        # Implement search functionality
        pass
```

### Configuration

CorpusFlow can be configured using either environment variables or a configuration file:

```yaml
# corpusflow.yaml
sources:
  google_docs:
    client_id: ${GOOGLE_CLIENT_ID}
    client_secret: ${GOOGLE_CLIENT_SECRET}
  office365:
    client_id: ${O365_CLIENT_ID}
    client_secret: ${O365_CLIENT_SECRET}
  s3:
    access_key: ${AWS_ACCESS_KEY}
    secret_key: ${AWS_SECRET_KEY}
    bucket: training-data
```

## 🔄 Processing Pipeline

CorpusFlow supports custom processing pipelines through middleware:

```python
from corpusflow import Pipeline, TextProcessor

# Create custom processor
class MyProcessor(TextProcessor):
    def process(self, document):
        # Implement processing logic
        return processed_document

# Create pipeline
pipeline = Pipeline([
    MyProcessor(),
    DeduplicationProcessor(),
    MetadataEnricher()
])

# Process documents
processed_docs = pipeline.process(documents)
```

## 🛡️ Authentication

CorpusFlow supports multiple authentication methods:

- OAuth 2.0 for Google Workspace and Office 365
- AWS credentials for S3
- API keys
- Custom authentication handlers

## 📊 Monitoring and Logging

Built-in support for monitoring and logging:

```python
from corpusflow import Monitor

monitor = Monitor()
doc_manager.set_monitor(monitor)

# Get processing stats
stats = monitor.get_stats()
print(f"Processed {stats.total_documents} documents")
print(f"Total size: {stats.total_size_gb:.2f} GB")
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install development dependencies
4. Run tests

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"
pytest
```

## 📝 License

This project is licensed under the Apache Version 2.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all contributors
- Built with inspiration from various open-source document processing tools
- Special thanks to the ML community for feedback and suggestions

## 📮 Contact

- GitHub Issues: For bug reports and feature requests
- Discussions: For questions and community support
- Email: jeff@check-ai.com

---

Built with ❤️ for the ML community