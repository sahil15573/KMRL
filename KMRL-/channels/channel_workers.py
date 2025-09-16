
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from imapclient import IMAPClient
import pyzmail
import shutil

class BaseChannelWorker:
    """Base class for all channel workers"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.staging_dir = config.get('staging_dir', './staging')
        os.makedirs(self.staging_dir, exist_ok=True)

    def process(self) -> List[Dict[str, Any]]:
        """Process files from this channel and return list of file info"""
        raise NotImplementedError

    def move_to_staging(self, source_path: str, meta_data: Dict[str, Any]) -> str:
        """Move file to staging area with meta_data"""
        filename = os.path.basename(source_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        staging_filename = f"{timestamp}_{self.name}_{filename}"
        staging_path = os.path.join(self.staging_dir, staging_filename)

        # Copy file to staging
        shutil.copy2(source_path, staging_path)

        # Save meta_data
        meta_data_path = staging_path + '.meta_data.json'
        with open(meta_data_path, 'w') as f:
            json.dump(meta_data, f, indent=2, default=str)

        return staging_path

class EmailChannelWorker(BaseChannelWorker):
    """Worker for processing emails via IMAP"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__('EMAIL', config)
        self.imap_host = config.get('imap_host')
        self.email = config.get('email')
        self.password = config.get('password')
        self.processed_emails_file = config.get('processed_emails_file', 'processed_emails.txt')
        self.filters = config.get('filters', {})

    def get_processed_emails(self) -> set:
        """Get list of already processed email UIDs"""
        if os.path.exists(self.processed_emails_file):
            with open(self.processed_emails_file, 'r') as f:
                return set(line.strip() for line in f)
        return set()

    def mark_email_processed(self, uid: str):
        """Mark email as processed"""
        with open(self.processed_emails_file, 'a') as f:
            f.write(f"{uid}\n")

    def process(self) -> List[Dict[str, Any]]:
        """Process new emails and return file information"""
        processed_files = []

        try:
            with IMAPClient(self.imap_host) as client:
                client.login(self.email, self.password)
                client.select_folder('INBOX')

                # Build search criteria
                search_criteria = ['ALL']
                if 'from' in self.filters:
                    search_criteria = ['FROM', self.filters['from']]
                if 'subject' in self.filters:
                    search_criteria.extend(['SUBJECT', self.filters['subject']])
                if 'since' in self.filters:
                    search_criteria.extend(['SINCE', self.filters['since']])

                # Get emails
                messages = client.search(search_criteria)
                processed_uids = self.get_processed_emails()

                for uid in messages:
                    uid_str = str(uid)
                    if uid_str in processed_uids:
                        continue

                    message_data = client.fetch([uid], ['RFC822'])
                    msg = pyzmail.PyzMessage.factory(message_data[uid][b'RFC822'])

                    # Save email body
                    body_text = ""
                    if msg.text_part:
                        body_text = msg.text_part.get_payload().decode(msg.text_part.charset or 'utf-8')
                    elif msg.html_part:
                        body_text = msg.html_part.get_payload().decode(msg.html_part.charset or 'utf-8')

                    if body_text:
                        body_filename = f"email_{uid}_body.txt"
                        body_path = os.path.join(self.staging_dir, body_filename)

                        with open(body_path, 'w', encoding='utf-8') as f:
                            f.write(body_text)

                        meta_data = {
                            'channel': 'EMAIL',
                            'email_uid': uid_str,
                            'subject': msg.get_subject(),
                            'sender': str(msg.get_addresses('from')),
                            'date': str(msg.get_date()),
                            'has_attachments': len(msg.mailparts) > 1
                        }

                        processed_files.append({
                            'filepath': body_path,
                            'meta_data': meta_data
                        })

                    # Save attachments
                    for part in msg.mailparts:
                        if part.filename:
                            attachment_path = os.path.join(self.staging_dir, f"email_{uid}_{part.filename}")
                            with open(attachment_path, 'wb') as f:
                                f.write(part.get_payload(decode=True))

                            meta_data = {
                                'channel': 'EMAIL',
                                'email_uid': uid_str,
                                'subject': msg.get_subject(),
                                'sender': str(msg.get_addresses('from')),
                                'date': str(msg.get_date()),
                                'attachment': True,
                                'original_filename': part.filename
                            }

                            processed_files.append({
                                'filepath': attachment_path,
                                'meta_data': meta_data
                            })

                    self.mark_email_processed(uid_str)

        except Exception as e:
            print(f"Error processing emails: {e}")

        return processed_files

class FileWatcherChannelWorker(BaseChannelWorker, FileSystemEventHandler):
    """Worker for monitoring file system directories (for scans, manual uploads)"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__('FILE_WATCHER', config)
        self.watch_directories = config.get('watch_directories', [])
        self.processed_files = set()
        self.new_files = []
        self.observer = Observer()

    def on_created(self, event):
        """Handle new file creation"""
        if not event.is_directory:
            filepath = event.src_path
            if self.is_valid_file(filepath) and filepath not in self.processed_files:
                # Wait a bit to ensure file is completely written
                time.sleep(1)

                meta_data = {
                    'channel': 'FILE_WATCHER',
                    'source_directory': os.path.dirname(filepath),
                    'detected_at': datetime.now().isoformat(),
                    'file_size': os.path.getsize(filepath) if os.path.exists(filepath) else 0
                }

                self.new_files.append({
                    'filepath': filepath,
                    'meta_data': meta_data
                })
                self.processed_files.add(filepath)

    def is_valid_file(self, filepath: str) -> bool:
        """Check if file should be processed"""
        valid_extensions = {'.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.tiff', '.dwg', '.dxf', '.txt', '.csv', '.xlsx'}
        _, ext = os.path.splitext(filepath.lower())
        return ext in valid_extensions and not os.path.basename(filepath).startswith('.')

    def start_watching(self):
        """Start monitoring directories"""
        for directory in self.watch_directories:
            if os.path.exists(directory):
                self.observer.schedule(self, directory, recursive=False)
                print(f"Watching directory: {directory}")

        self.observer.start()

    def stop_watching(self):
        """Stop monitoring directories"""
        self.observer.stop()
        self.observer.join()

    def process(self) -> List[Dict[str, Any]]:
        """Return new files found"""
        current_files = self.new_files.copy()
        self.new_files.clear()
        return current_files

class SharePointChannelWorker(BaseChannelWorker):
    """Worker for SharePoint document libraries (placeholder implementation)"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__('SHAREPOINT', config)
        self.site_url = config.get('site_url')
        self.library_name = config.get('library_name')
        # In real implementation, you would use Office365-REST-Python-Client
        # or similar library

    def process(self) -> List[Dict[str, Any]]:
        """Process SharePoint files (placeholder)"""
        # This would connect to SharePoint, download new/modified files
        # For now, return empty list
        print("SharePoint worker not fully implemented - placeholder")
        return []

class ManualUploadChannelWorker(BaseChannelWorker):
    """Worker for manual file uploads"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__('MANUAL_UPLOAD', config)
        self.upload_directory = config.get('upload_directory', './uploads')
        os.makedirs(self.upload_directory, exist_ok=True)
        self.processed_files = set()

    def process(self) -> List[Dict[str, Any]]:
        """Process files in upload directory"""
        processed_files = []

        for filename in os.listdir(self.upload_directory):
            filepath = os.path.join(self.upload_directory, filename)

            if os.path.isfile(filepath) and filepath not in self.processed_files:
                meta_data = {
                    'channel': 'MANUAL_UPLOAD',
                    'uploaded_at': datetime.now().isoformat(),
                    'file_size': os.path.getsize(filepath)
                }

                processed_files.append({
                    'filepath': filepath,
                    'meta_data': meta_data
                })
                self.processed_files.add(filepath)

        return processed_files

class ChannelManager:
    """Manages all channel workers"""

    def __init__(self, config: Dict[str, Any]):
        self.workers = {}
        self.config = config

        # Initialize workers based on config
        if 'email' in config:
            self.workers['email'] = EmailChannelWorker(config['email'])

        if 'file_watcher' in config:
            worker = FileWatcherChannelWorker(config['file_watcher'])
            self.workers['file_watcher'] = worker
            worker.start_watching()

        if 'sharepoint' in config:
            self.workers['sharepoint'] = SharePointChannelWorker(config['sharepoint'])

        if 'manual_upload' in config:
            self.workers['manual_upload'] = ManualUploadChannelWorker(config['manual_upload'])

    def process_all_channels(self) -> List[Dict[str, Any]]:
        """Process all channels and return all new files"""
        all_files = []

        for name, worker in self.workers.items():
            try:
                files = worker.process()
                all_files.extend(files)
                if files:
                    print(f"Channel {name}: Found {len(files)} new files")
            except Exception as e:
                print(f"Error processing channel {name}: {e}")

        return all_files

    def stop_all(self):
        """Stop all workers"""
        for worker in self.workers.values():
            if hasattr(worker, 'stop_watching'):
                worker.stop_watching()
