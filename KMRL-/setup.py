#!/usr/bin/env python3
"""
Setup script for KMRL Document Ingestion System
"""

import os
import sys
import subprocess

def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

def setup_tesseract():
    """Setup Tesseract OCR"""
    print("Setting up Tesseract OCR...")
    print("Please install Tesseract OCR manually:")
    print("- Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-mal")
    print("- CentOS/RHEL: sudo yum install tesseract tesseract-langpack-mal")
    print("- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
    print("- macOS: brew install tesseract tesseract-lang")

def setup_poppler():
    """Setup Poppler for PDF processing"""
    print("Setting up Poppler for PDF processing...")
    print("Please install Poppler manually:")
    print("- Ubuntu/Debian: sudo apt-get install poppler-utils")
    print("- CentOS/RHEL: sudo yum install poppler-utils")
    print("- Windows: Download from https://poppler.freedesktop.org/")
    print("- macOS: brew install poppler")

def create_directories():
    """Create necessary directories"""
    dirs = [
        'staging',
        'staging/email',
        'staging/file_watcher', 
        'staging/manual',
        'staging/sharepoint',
        'logs',
        'uploads',
        'watch_scans',
        'watch_uploads',
        'watch_cad'
    ]

    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"Created directory: {dir_name}")

def create_env_file():
    """Create environment file template"""
    env_content = """# KMRL Document Ingestion System Environment Variables

# Database
DATABASE_URL=sqlite:///kmrl_documents.db

# Email Configuration
IMAP_HOST=imap.gmail.com
EMAIL_USERNAME=your_email@example.com
EMAIL_PASSWORD=your_password

# SharePoint Configuration (optional)
SHAREPOINT_SITE_URL=https://yourcompany.sharepoint.com/sites/yoursite
SHAREPOINT_LIBRARY=Documents

# Logging
LOG_LEVEL=INFO
"""

    with open('.env.example', 'w') as f:
        f.write(env_content)
    print("Created .env.example file")

def main():
    print("Setting up KMRL Document Ingestion System...")
    print("="*50)

    # Install Python requirements
    try:
        install_requirements()
        print("✅ Python requirements installed")
    except Exception as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

    # Create directories
    create_directories()
    print("✅ Directories created")

    # Create environment file
    create_env_file()
    print("✅ Environment template created")

    # Setup instructions for external dependencies
    print("\n" + "="*50)
    print("MANUAL SETUP REQUIRED:")
    print("="*50)
    setup_tesseract()
    print()
    setup_poppler()

    print("\n" + "="*50)
    print("SETUP COMPLETE!")
    print("="*50)
    print("Next steps:")
    print("1. Install Tesseract OCR and Poppler (see above)")
    print("2. Copy .env.example to .env and configure your settings")
    print("3. Test the system: python main.py test")
    print("4. Run the system: python main.py run")

    return True

if __name__ == "__main__":
    main()
