
import os
import json
from datetime import datetime
from typing import Dict, List, Any
from sqlalchemy.orm import Session

# Import our modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Document, ProcessingQueue, get_database_session
from utils.file_detector import FileTypeDetector
from extractors.extractors import ExtractorFactory
from classifiers.department_classifier import DepartmentClassifier

class DocumentDispatcher:
    """Central dispatcher for processing documents from all channels"""

    def __init__(self):
        self.file_detector = FileTypeDetector()
        self.department_classifier = DepartmentClassifier()
        self.processing_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'by_channel': {},
            'by_type': {},
            'by_department': {}
        }

    def process_file(self, filepath: str, meta_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single file through the entire pipeline
        Returns processing result with status and details
        """
        result = {
            'filepath': filepath,
            'status': 'PROCESSING',
            'document_id': None,
            'error': None,
            'processing_steps': []
        }

        try:
            # Step 1: File type detection
            file_type, mime_type = self.file_detector.detect_file_type(filepath)
            result['processing_steps'].append(f"Detected file type: {file_type} ({mime_type})")

            if not self.file_detector.is_supported_type(file_type):
                result['status'] = 'UNSUPPORTED'
                result['error'] = f"File type {file_type} is not supported"
                return result

            # Step 2: Create database record
            db_session = get_database_session()
            try:
                document = Document(
                    filename=os.path.basename(filepath),
                    original_path=filepath,
                    file_type=file_type,
                    mime_type=mime_type,
                    channel=meta_data.get('channel', 'UNKNOWN'),
                    meta_data=json.dumps(meta_data),
                    status='PROCESSING'
                )

                db_session.add(document)
                db_session.commit()
                result['document_id'] = document.id
                result['processing_steps'].append(f"Created database record: ID {document.id}")

            except Exception as e:
                db_session.rollback()
                raise e

            # Step 3: Text extraction
            try:
                extractor = ExtractorFactory.get_extractor(file_type)
                extraction_result = extractor.extract(filepath)

                extracted_text = extraction_result.get('text', '')
                extraction_meta_data = extraction_result.get('meta_data', {})

                result['processing_steps'].append(f"Extracted {len(extracted_text)} characters")

                # Handle extraction errors
                if 'error' in extraction_meta_data:
                    result['processing_steps'].append(f"Extraction warning: {extraction_meta_data['error']}")

            except Exception as e:
                result['status'] = 'EXTRACTION_FAILED'
                result['error'] = f"Text extraction failed: {str(e)}"

                # Update database
                document.status = 'ERROR'
                document.error_message = result['error']
                db_session.commit()
                db_session.close()

                return result

            # Step 4: Department classification
            classification_result = self.department_classifier.classify(
                text=extracted_text,
                filename=os.path.basename(filepath),
                meta_data={'file_type': file_type, **meta_data}
            )

            department = classification_result.get('department', 'UNKNOWN')
            confidence = classification_result.get('confidence', 0.0)

            result['processing_steps'].append(
                f"Classified as {department} (confidence: {confidence:.2f})"
            )

            # Step 5: Update database with final results
            document.extracted_text = extracted_text
            document.department = department
            document.status = 'PROCESSED'

            # Merge meta_data
            final_meta_data = {
                **meta_data,
                'extraction_meta_data': extraction_meta_data,
                'classification': classification_result,
                'processing_timestamp': datetime.utcnow().isoformat()
            }
            document.meta_data = json.dumps(final_meta_data)

            db_session.commit()
            db_session.close()

            result['status'] = 'SUCCESS'
            result['department'] = department
            result['processing_steps'].append("Processing completed successfully")

            # Update stats
            self.update_stats(meta_data.get('channel', 'UNKNOWN'), file_type, department, True)

        except Exception as e:
            result['status'] = 'FAILED'
            result['error'] = f"Processing failed: {str(e)}"
            result['processing_steps'].append(f"Error: {str(e)}")

            # Update database if document was created
            if result['document_id']:
                try:
                    db_session = get_database_session()
                    document = db_session.query(Document).filter_by(id=result['document_id']).first()
                    if document:
                        document.status = 'ERROR'
                        document.error_message = str(e)
                        db_session.commit()
                    db_session.close()
                except:
                    pass  # Don't fail on database update errors

            # Update stats
            self.update_stats(meta_data.get('channel', 'UNKNOWN'), file_type, 'UNKNOWN', False)

        return result

    def process_batch(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of files
        files: List of {'filepath': str, 'meta_data': dict}
        """
        results = []

        print(f"Processing batch of {len(files)} files...")

        for i, file_info in enumerate(files, 1):
            filepath = file_info['filepath']
            meta_data = file_info.get('meta_data', {})

            print(f"[{i}/{len(files)}] Processing: {os.path.basename(filepath)}")

            result = self.process_file(filepath, meta_data)
            results.append(result)

            # Print result summary
            if result['status'] == 'SUCCESS':
                print(f"  ✅ Success - Department: {result.get('department', 'N/A')}")
            else:
                print(f"  ❌ {result['status']}: {result.get('error', 'Unknown error')}")

        self.processing_stats['total_processed'] += len(files)

        return results

    def update_stats(self, channel: str, file_type: str, department: str, success: bool):
        """Update processing statistics"""
        if success:
            self.processing_stats['successful'] += 1
        else:
            self.processing_stats['failed'] += 1

        # Update by channel
        if channel not in self.processing_stats['by_channel']:
            self.processing_stats['by_channel'][channel] = 0
        self.processing_stats['by_channel'][channel] += 1

        # Update by type
        if file_type not in self.processing_stats['by_type']:
            self.processing_stats['by_type'][file_type] = 0
        self.processing_stats['by_type'][file_type] += 1

        # Update by department
        if department not in self.processing_stats['by_department']:
            self.processing_stats['by_department'][department] = 0
        self.processing_stats['by_department'][department] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return self.processing_stats.copy()

    def reset_stats(self):
        """Reset processing statistics"""
        self.processing_stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'by_channel': {},
            'by_type': {},
            'by_department': {}
        }

    def get_document_by_id(self, document_id: int) -> Dict[str, Any]:
        """Retrieve document information by ID"""
        db_session = get_database_session()
        try:
            document = db_session.query(Document).filter_by(id=document_id).first()
            if document:
                return {
                    'id': document.id,
                    'filename': document.filename,
                    'file_type': document.file_type,
                    'channel': document.channel,
                    'department': document.department,
                    'extracted_text': document.extracted_text,
                    'meta_data': json.loads(document.meta_data) if document.meta_data else {},
                    'status': document.status,
                    'processed_at': document.processed_at,
                    'error_message': document.error_message
                }
            else:
                return None
        finally:
            db_session.close()

    def search_documents(self, query: str = None, department: str = None, 
                        file_type: str = None, channel: str = None,
                        limit: int = 50) -> List[Dict[str, Any]]:
        """Search documents with various filters"""
        db_session = get_database_session()
        try:
            query_obj = db_session.query(Document)

            # Apply filters
            if query:
                query_obj = query_obj.filter(Document.extracted_text.contains(query))
            if department:
                query_obj = query_obj.filter(Document.department == department)
            if file_type:
                query_obj = query_obj.filter(Document.file_type == file_type)
            if channel:
                query_obj = query_obj.filter(Document.channel == channel)

            documents = query_obj.order_by(Document.processed_at.desc()).limit(limit).all()

            results = []
            for doc in documents:
                results.append({
                    'id': doc.id,
                    'filename': doc.filename,
                    'file_type': doc.file_type,
                    'channel': doc.channel,
                    'department': doc.department,
                    'status': doc.status,
                    'processed_at': doc.processed_at,
                    'text_preview': doc.extracted_text[:200] + '...' if doc.extracted_text else ''
                })

            return results
        finally:
            db_session.close()
