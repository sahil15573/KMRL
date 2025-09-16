
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(500), nullable=False)
    original_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)  # PDF, DOCX, IMAGE, etc.
    mime_type = Column(String(100), nullable=False)
    channel = Column(String(50), nullable=False)  # EMAIL, SCAN, MANUAL, etc.
    department = Column(String(100))  # Classified department
    extracted_text = Column(Text)
    meta_data = Column(Text)  # JSON string with additional info
    processed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default='PENDING')  # PENDING, PROCESSED, ERROR
    error_message = Column(Text)

class ProcessingQueue(Base):
    __tablename__ = 'processing_queue'

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, nullable=False)
    task_type = Column(String(50), nullable=False)  # EXTRACT, CLASSIFY, SUMMARIZE
    priority = Column(Integer, default=1)
    status = Column(String(50), default='QUEUED')
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

# Database connection
def get_database_session():
    database_url = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_h5POWHDx2YQa@ep-ancient-tooth-a17uz6cz-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require')
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
