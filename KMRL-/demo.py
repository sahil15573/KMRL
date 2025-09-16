#!/usr/bin/env python3
"""
Demo script for KMRL Document Ingestion System
Shows basic usage and functionality
"""

import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dispatcher import DocumentDispatcher
from utils.file_detector import FileTypeDetector
from classifiers.department_classifier import DepartmentClassifier

def create_demo_files():
    """Create some demo files for testing"""
    demo_dir = './demo_files'
    os.makedirs(demo_dir, exist_ok=True)

    # Create demo text files
    demo_files = {
        'engineering_report.txt': """
        KMRL Engineering Technical Report

        Track Maintenance Schedule - Line 1
        Date: September 2025

        Rail inspection completed on sections 1A through 1C.
        Minor rail wear detected at station approach areas.
        Ballast cleaning required at KM 5+200.
        Signal system functioning normally.
        Overhead catenary tension checked and adjusted.

        Recommendations:
        1. Schedule ballast replacement by October 2025
        2. Monitor rail wear patterns monthly
        3. Update maintenance drawings DWG-001-Rev3
        """,

        'procurement_invoice.txt': """
        KMRL Procurement Department

        Invoice Processing Notice
        Vendor: ABC Rail Components Ltd
        PO Number: PO-2025-0156
        Invoice No: INV-789123
        Amount: ₹15,50,000

        Items:
        - Rail fasteners: 2000 units
        - Sleeper bolts: 5000 units  
        - Track pads: 1000 units

        Payment terms: Net 30 days
        Delivery scheduled: 15th October 2025
        Contact: procurement@kmrl.co.in
        """,

        'safety_incident.txt': """
        KMRL Safety Department - Incident Report

        Incident ID: INC-2025-0045
        Date: 10th September 2025
        Location: Aluva Station - Platform 2

        Description:
        Minor slip incident during platform cleaning.
        No injuries reported. Wet floor signage was missing.
        Immediate corrective action taken.

        Investigation findings:
        - Cleaning protocol not followed completely
        - Warning signs not deployed
        - Staff training update required

        Recommendations:
        1. Retrain cleaning staff on safety procedures
        2. Audit safety equipment weekly
        3. Update safety manual Section 4.2
        """
    }

    for filename, content in demo_files.items():
        filepath = os.path.join(demo_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)

    return [os.path.join(demo_dir, f) for f in demo_files.keys()]

def demo_file_detection():
    """Demonstrate file type detection"""
    print("\n" + "="*60)
    print("FILE TYPE DETECTION DEMO")
    print("="*60)

    detector = FileTypeDetector()
    demo_files = create_demo_files()

    for filepath in demo_files:
        file_type, mime_type = detector.detect_file_type(filepath)
        filename = os.path.basename(filepath)
        print(f"File: {filename}")
        print(f"  Type: {file_type}")  
        print(f"  MIME: {mime_type}")
        print(f"  Supported: {detector.is_supported_type(file_type)}")
        print()

def demo_classification():
    """Demonstrate department classification"""
    print("\n" + "="*60) 
    print("DEPARTMENT CLASSIFICATION DEMO")
    print("="*60)

    classifier = DepartmentClassifier()
    demo_files = create_demo_files()

    for filepath in demo_files:
        with open(filepath, 'r') as f:
            content = f.read()

        result = classifier.classify(content, os.path.basename(filepath))

        print(f"File: {os.path.basename(filepath)}")
        print(f"  Department: {result['department']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Reasoning: {result['reasoning'][:2]}")  # Show first 2 reasons
        print()

def demo_full_processing():
    """Demonstrate full document processing pipeline"""
    print("\n" + "="*60)
    print("FULL PROCESSING PIPELINE DEMO") 
    print("="*60)

    dispatcher = DocumentDispatcher()
    demo_files = create_demo_files()

    # Process each file
    for filepath in demo_files:
        print(f"Processing: {os.path.basename(filepath)}")

        meta_data = {
            'channel': 'DEMO',
            'uploaded_by': 'demo_script',
            'timestamp': datetime.now().isoformat()
        }

        result = dispatcher.process_file(filepath, meta_data)

        print(f"  Status: {result['status']}")
        if result['status'] == 'SUCCESS':
            print(f"  Department: {result.get('department', 'N/A')}")
            print(f"  Document ID: {result.get('document_id', 'N/A')}")
        else:
            print(f"  Error: {result.get('error', 'Unknown')}")
        print()

    # Show processing statistics
    stats = dispatcher.get_stats()
    print("Processing Statistics:")
    print(f"  Total: {stats['total_processed']}")
    print(f"  Successful: {stats['successful']}")  
    print(f"  Failed: {stats['failed']}")

    if stats['by_department']:
        print("  By Department:")
        for dept, count in stats['by_department'].items():
            print(f"    {dept}: {count}")

def demo_search():
    """Demonstrate document search"""
    print("\n" + "="*60)
    print("DOCUMENT SEARCH DEMO")
    print("="*60)

    dispatcher = DocumentDispatcher()

    # Search examples
    search_queries = [
        {'query': 'safety', 'description': 'Documents containing "safety"'},
        {'department': 'ENGINEERING', 'description': 'All engineering documents'},
        {'file_type': 'TXT', 'description': 'All text files'},
        {'query': 'maintenance', 'department': 'ENGINEERING', 'description': 'Engineering maintenance documents'}
    ]

    for search in search_queries:
        print(f"Search: {search['description']}")

        results = dispatcher.search_documents(**{k: v for k, v in search.items() if k != 'description'})

        print(f"  Found: {len(results)} documents")
        for result in results[:3]:  # Show first 3 results
            print(f"    - {result['filename']} ({result['department']}) - {result['file_type']}")

        if len(results) > 3:
            print(f"    ... and {len(results) - 3} more")
        print()

def main():
    """Run all demos"""
    print("KMRL DOCUMENT INGESTION SYSTEM - DEMO")
    print("="*60)
    print("This demo will show the key features of the document processing system.")
    print()

    try:
        # Run demos
        demo_file_detection()
        demo_classification() 
        demo_full_processing()
        demo_search()

        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("The system has processed the demo files and stored them in the database.")
        print("You can now:")
        print("1. Run 'python main.py status' to see overall statistics")
        print("2. Run 'python main.py run' to start continuous processing")
        print("3. Add files to ./watch_uploads/ to see live processing")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\nTry running 'python main.py test' to check system configuration")

if __name__ == "__main__":
    main()
