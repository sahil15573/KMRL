
import magic
import os
from typing import Tuple

class FileTypeDetector:
    """Detects file types using python-magic and fallback to extensions"""

    def __init__(self):
        self.mime_to_type_mapping = {
            # PDF files
            'application/pdf': 'PDF',

            # Microsoft Office documents
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PPTX',
            'application/msword': 'DOC',
            'application/vnd.ms-excel': 'XLS',

            # Images
            'image/jpeg': 'IMAGE',
            'image/jpg': 'IMAGE',
            'image/png': 'IMAGE',
            'image/tiff': 'IMAGE',
            'image/bmp': 'IMAGE',
            'image/gif': 'IMAGE',

            # CAD files
            'image/vnd.dwg': 'DWG',
            'application/acad': 'DWG',
            'application/x-dwg': 'DWG',
            'application/dwg': 'DWG',
            'image/vnd.dxf': 'DXF',
            'application/dxf': 'DXF',

            # Text and CSV
            'text/plain': 'TXT',
            'text/csv': 'CSV',

            # Archives
            'application/zip': 'ZIP',
            'application/x-rar-compressed': 'RAR',
        }

        self.extension_mapping = {
            '.pdf': 'PDF',
            '.docx': 'DOCX',
            '.doc': 'DOC',
            '.xlsx': 'XLSX',
            '.xls': 'XLS',
            '.pptx': 'PPTX',
            '.jpg': 'IMAGE',
            '.jpeg': 'IMAGE',
            '.png': 'IMAGE',
            '.tiff': 'IMAGE',
            '.tif': 'IMAGE',
            '.bmp': 'IMAGE',
            '.gif': 'IMAGE',
            '.dwg': 'DWG',
            '.dxf': 'DXF',
            '.txt': 'TXT',
            '.csv': 'CSV',
            '.zip': 'ZIP',
            '.rar': 'RAR',
        }

    def detect_file_type(self, filepath: str) -> Tuple[str, str]:
        """
        Detect file type and MIME type
        Returns: (file_type, mime_type)
        """
        try:
            # Get MIME type using magic
            mime_type = magic.from_file(filepath, mime=True)

            # Get file extension as fallback
            _, ext = os.path.splitext(filepath)
            ext = ext.lower()

            # Try to map MIME type first
            if mime_type in self.mime_to_type_mapping:
                file_type = self.mime_to_type_mapping[mime_type]
            elif ext in self.extension_mapping:
                file_type = self.extension_mapping[ext]
            else:
                # Special handling for some formats
                if 'dwg' in mime_type.lower() or ext == '.dwg':
                    file_type = 'DWG'
                elif 'dxf' in mime_type.lower() or ext == '.dxf':
                    file_type = 'DXF'
                elif mime_type.startswith('image/'):
                    file_type = 'IMAGE'
                elif mime_type.startswith('text/'):
                    file_type = 'TXT'
                else:
                    file_type = 'UNKNOWN'

            return file_type, mime_type

        except Exception as e:
            print(f"Error detecting file type for {filepath}: {e}")
            # Fallback to extension only
            _, ext = os.path.splitext(filepath)
            ext = ext.lower()
            file_type = self.extension_mapping.get(ext, 'UNKNOWN')
            return file_type, 'application/octet-stream'

    def is_supported_type(self, file_type: str) -> bool:
        """Check if file type is supported for processing"""
        supported_types = ['PDF', 'DOCX', 'DOC', 'IMAGE', 'DWG', 'DXF', 'TXT', 'CSV', 'XLSX']
        return file_type in supported_types
