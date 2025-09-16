
# Configuration for KMRL Document Ingestion System
import os

# Database Configuration
DATABASE_CONFIG = {
    'url': os.getenv('DATABASE_URL', 'sqlite:///kmrl_documents.db')
}

# Channel Configurations
CHANNEL_CONFIG = {
    # 'email': {
    #     'imap_host': os.getenv('IMAP_HOST', 'imap.gmail.com'),
    #     'email': os.getenv('EMAIL_USERNAME', 'your_email@example.com'),
    #     'password': os.getenv('EMAIL_PASSWORD', 'your_password'),
    #     'staging_dir': './staging/email',
    #     'processed_emails_file': './processed_emails.txt',
    #     'filters': {
    #         # 'from': 'sender@example.com',
    #         # 'subject': 'Important',
    #         # 'since': '01-Sep-2025'
    #     }
    # },

    # 'file_watcher': {
    #     'watch_directories': [
    #         './watch_scans',      # Scanned documents
    #         './watch_uploads',    # Manual uploads
    #         './watch_cad'        # CAD files
    #     ],
    #     'staging_dir': './staging/file_watcher'
    # },

    'manual_upload': {
        'upload_directory': './uploads',
        'staging_dir': './staging/manual'
    },

    # 'sharepoint': {
    #     'site_url': os.getenv('SHAREPOINT_SITE_URL', ''),
    #     'library_name': os.getenv('SHAREPOINT_LIBRARY', 'Documents'),
    #     'staging_dir': './staging/sharepoint'
    # }
}

# Processing Configuration
PROCESSING_CONFIG = {
    'batch_size': 10,
    'max_file_size_mb': 50,
    'supported_extensions': ['.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.tiff', '.dwg', '.dxf', '.txt', '.csv', '.xlsx'],
    'ocr_languages': 'eng+mal',  # English + Malayalam
    'cleanup_staging': True,
    'processing_interval_seconds': 30
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': './logs/document_ingestion.log'
}
