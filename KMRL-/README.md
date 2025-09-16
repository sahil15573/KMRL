# KMRL Document Ingestion System

A comprehensive document processing system designed for Kochi Metro Rail Limited (KMRL) to handle document overload across multiple channels with intelligent extraction, classification, and routing.

## Features

🔄 **Multi-Source Ingestion**
- Email attachments (IMAP)
- File system monitoring (scans, uploads)
- SharePoint integration (placeholder)
- Manual file uploads

🔍 **Intelligent File Processing**
- Automatic file type detection using python-magic
- Format-specific extractors (PDF, DOCX, Images, CAD files)
- OCR for scanned documents with Malayalam + English support
- Table extraction from PDFs and spreadsheets

🏢 **Department Classification**
- Rule-based classification system
- Automatic routing to: Engineering, Procurement, HR, Finance, Safety, Operations, Legal, Regulatory
- Confidence scoring and reasoning

📊 **Database Storage**
- SQLAlchemy-based data persistence
- Full-text search capabilities
- Processing statistics and audit trails
- Metadata preservation

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│   Input         │    │   Processing     │    │   Output           │
│   Channels      │    │   Pipeline       │    │   & Storage        │
├─────────────────┤    ├──────────────────┤    ├────────────────────┤
│ • Email (IMAP)  │───▶│ 1. File Type     │───▶│ • SQLite/PostgreSQL│
│ • File Watcher  │    │    Detection     │    │ • Full-text Search │
│ • Manual Upload │    │ 2. Text Extract. │    │ • Department Tags  │
│ • SharePoint    │    │ 3. Classification│    │ • Processing Stats │
└─────────────────┘    │ 4. Dept. Routing │    └────────────────────┘
                       └──────────────────┘
```

## Installation

### 1. Clone and Setup
```bash
cd document_ingestion_system
python setup.py
```

### 2. Install External Dependencies

**Tesseract OCR (for scanned documents):**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-mal

# CentOS/RHEL  
sudo yum install tesseract tesseract-langpack-mal

# Windows
Download from: https://github.com/UB-Mannheim/tesseract/wiki

# macOS
brew install tesseract tesseract-lang
```

**Poppler (for PDF to image conversion):**
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows  
Download from: https://poppler.freedesktop.org/

# macOS
brew install poppler
```

### 3. Configuration
```bash
cp .env.example .env
# Edit .env with your email and database settings
```

## Usage

### Test System Configuration
```bash
python main.py test
```

### Run Once (Process Current Files)
```bash
python main.py once
```

### Run Continuously (Monitor Channels)
```bash
python main.py run
```

### Check Status
```bash
python main.py status
```

## File Type Support

| Type | Extensions | Extractor | Features |
|------|------------|-----------|----------|
| PDF  | .pdf | pdfplumber + OCR fallback | Text + Tables + Images |
| Office | .docx, .xlsx | python-docx, pandas | Text + Tables |  
| Images | .jpg, .png, .tiff | Tesseract OCR | Malayalam + English |
| CAD | .dwg, .dxf | ezdxf | Text entities + Metadata |
| Text | .txt, .csv | Native | Full content |

## Department Classification

The system automatically classifies documents into:

- **ENGINEERING**: CAD files, technical specs, maintenance reports
- **PROCUREMENT**: Purchase orders, vendor communications, invoices
- **HR**: Employee documents, policies, training materials
- **FINANCE**: Budget reports, financial statements, audits
- **SAFETY**: Incident reports, safety manuals, compliance docs
- **OPERATIONS**: Service reports, schedules, performance data
- **LEGAL**: Contracts, agreements, legal opinions
- **REGULATORY**: Government directives, compliance updates

## Configuration

### Email Channel
```python
'email': {
    'imap_host': 'imap.gmail.com',
    'email': 'your_email@example.com', 
    'password': 'your_password',
    'filters': {
        'from': 'sender@example.com',
        'subject': 'Important',
        'since': '01-Sep-2025'
    }
}
```

### File Watcher
```python
'file_watcher': {
    'watch_directories': [
        './watch_scans',      # Scanned documents
        './watch_uploads',    # Manual uploads  
        './watch_cad'        # CAD files
    ]
}
```

## API Usage

```python
from dispatcher import DocumentDispatcher
from utils.file_detector import FileTypeDetector

# Initialize dispatcher
dispatcher = DocumentDispatcher()

# Process single file
result = dispatcher.process_file('document.pdf', {
    'channel': 'MANUAL',
    'uploader': 'john.doe'
})

# Search documents
results = dispatcher.search_documents(
    query='safety report',
    department='SAFETY',
    limit=10
)
```

## Database Schema

### Documents Table
- `id`: Primary key
- `filename`: Original filename  
- `file_type`: Detected type (PDF, IMAGE, etc.)
- `channel`: Source channel (EMAIL, FILE_WATCHER, etc.)
- `department`: Classified department
- `extracted_text`: Full extracted content
- `metadata`: JSON metadata and processing info
- `status`: PROCESSING, PROCESSED, ERROR
- `processed_at`: Timestamp

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## License

This project is designed for KMRL internal use and educational purposes.

## Support

For issues and questions:
1. Check the logs in `./logs/document_ingestion.log`
2. Run `python main.py test` to diagnose configuration issues
3. Review the processing statistics with `python main.py status`

---

**Built for KMRL Document Overload Solution - SIH 2025**
