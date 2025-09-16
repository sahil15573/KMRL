
#!/usr/bin/env python3
"""
KMRL Document Ingestion System - Main Orchestrator
Coordinates all channels, processing, and storage
"""
from dotenv import load_dotenv
load_dotenv()
print("entetred main")
import os
print("db_used",os.getenv("DATABASE_URL"))

import sys
import time
import logging
import signal
from typing import Dict, Any
from datetime import datetime
print("entetred main 2")
# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import CHANNEL_CONFIG, PROCESSING_CONFIG, LOGGING_CONFIG
from channels.channel_workers import ChannelManager
from dispatcher import DocumentDispatcher

class DocumentIngestionOrchestrator:
    """Main orchestrator for the document ingestion system"""

    def __init__(self):
        self.setup_logging()
        self.setup_directories()

        self.channel_manager = ChannelManager(CHANNEL_CONFIG)
        self.dispatcher = DocumentDispatcher()

        self.running = True
        self.processing_interval = PROCESSING_CONFIG.get('processing_interval_seconds', 30)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.logger = logging.getLogger(__name__)
        self.logger.info("Document Ingestion System initialized")

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = os.path.dirname(LOGGING_CONFIG.get('file', './logs/document_ingestion.log'))
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, LOGGING_CONFIG.get('level', 'INFO')),
            format=LOGGING_CONFIG.get('format', '%(asctime)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.FileHandler(LOGGING_CONFIG.get('file', './logs/document_ingestion.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def setup_directories(self):
        """Create necessary directories"""
        directories = [
            './staging',
            './logs',
            './uploads',
            './watch_scans',
            './watch_uploads', 
            './watch_cad'
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def run_once(self):
        """Run one processing cycle"""
        self.logger.info("Starting processing cycle...")

        try:
            # Get new files from all channels
            new_files = self.channel_manager.process_all_channels()

            if new_files:
                self.logger.info(f"Found {len(new_files)} new files to process")
                print("entered new files")
                # Process files in batches
                batch_size = PROCESSING_CONFIG.get('batch_size', 10)

                for i in range(0, len(new_files), batch_size):
                    batch = new_files[i:i + batch_size]
                    self.logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} files)")

                    results = self.dispatcher.process_batch(batch)

                    # Log batch results
                    successful = sum(1 for r in results if r['status'] == 'SUCCESS')
                    failed = len(results) - successful

                    self.logger.info(f"Batch complete: {successful} successful, {failed} failed")

                    if failed > 0:
                        for result in results:
                            if result['status'] != 'SUCCESS':
                                self.logger.error(f"Failed to process {result['filepath']}: {result.get('error', 'Unknown error')}")
            else:
                self.logger.debug("No new files found")

        except Exception as e:
            self.logger.error(f"Error in processing cycle: {e}", exc_info=True)

    def run_continuous(self):
        """Run the system continuously"""
        self.logger.info(f"Starting continuous processing (interval: {self.processing_interval}s)")

        while self.running:
            cycle_start = time.time()

            try:
                self.run_once()
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}", exc_info=True)

            # Wait for next cycle
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, self.processing_interval - cycle_duration)

            if sleep_time > 0:
                time.sleep(sleep_time)

        self.shutdown()

    def shutdown(self):
        """Shutdown the system gracefully"""
        self.logger.info("Shutting down...")

        try:
            self.channel_manager.stop_all()
            stats = self.dispatcher.get_stats()
            self.logger.info(f"Final processing stats: {stats}")
            print("entered shutdown")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

        self.logger.info("Shutdown complete")

    def print_status(self):
        """Print system status and statistics"""
        stats = self.dispatcher.get_stats()

        print("\n" + "="*50)
        print("KMRL DOCUMENT INGESTION SYSTEM STATUS")
        print("="*50)
        print(f"Total processed: {stats['total_processed']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")

        if stats['by_channel']:
            print("\nBy Channel:")
            for channel, count in stats['by_channel'].items():
                print(f"  {channel}: {count}")

        if stats['by_type']:
            print("\nBy File Type:")
            for file_type, count in stats['by_type'].items():
                print(f"  {file_type}: {count}")

        if stats['by_department']:
            print("\nBy Department:")
            for dept, count in stats['by_department'].items():
                print(f"  {dept}: {count}")

        print("="*50 + "\n")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        orchestrator = DocumentIngestionOrchestrator()

        if command == "run":
            # Run continuously
            orchestrator.run_continuous()

        elif command == "once":
            # Run once and exit
            orchestrator.run_once()
            orchestrator.print_status()

        elif command == "status":
            # Show status only
            orchestrator.print_status()

        elif command == "test":
            # Test mode - check configuration and connections
            print("Testing system configuration...")

            # Test database connection
            try:
                from database.models import get_database_session
                session = get_database_session()
                session.close()
                print("✅ Database connection: OK")
            except Exception as e:
                print(f"❌ Database connection: FAILED - {e}")

            # Test file detection
            try:
                from utils.file_detector import FileTypeDetector
                detector = FileTypeDetector()
                print("✅ File type detector: OK")
            except Exception as e:
                print(f"❌ File type detector: FAILED - {e}")

            # Test extractors
            try:
                from extractors.extractors import ExtractorFactory
                extractor = ExtractorFactory.get_extractor('PDF')
                print("✅ Extractors: OK")
            except Exception as e:
                print(f"❌ Extractors: FAILED - {e}")

            # Test classifier
            try:
                from classifiers.department_classifier import DepartmentClassifier
                classifier = DepartmentClassifier()
                print("✅ Department classifier: OK")
            except Exception as e:
                print(f"❌ Department classifier: FAILED - {e}")

            orchestrator.print_status()

        else:
            print(f"Unknown command: {command}")
            print("Available commands: run, once, status, test")

    else:
        print("KMRL Document Ingestion System")
        print("Usage: python main.py <command>")
        print("Commands:")
        print("  run     - Run continuously")
        print("  once    - Run once and exit")
        print("  status  - Show current status")
        print("  test    - Test system configuration")

if __name__ == "__main__":
    main()
