"""
Document API endpoints
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime
from app.db.session import get_db
from app.models.document import Document
from app.models.fund import Fund
from app.schemas.document import (
    Document as DocumentSchema,
    DocumentUploadResponse,
    DocumentStatus
)
from app.tasks.document_tasks import process_document_task
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    fund_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and process a PDF document.

    The document will be processed asynchronously by a Celery worker.
    """

    # Log received fund_id for debugging
    logger.info(f"Upload request received - file: {file.filename}, fund_id: {fund_id}")

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes"
        )

    # If fund_id is not provided, create a default fund
    if not fund_id:
        # Check if default fund exists
        default_fund = db.query(Fund).filter(Fund.name == "Default Fund").first()
        if not default_fund:
            default_fund = Fund(
                name="Default Fund",
                gp_name="Unknown GP",
                fund_type="Unknown",
                vintage_year=datetime.now().year
            )
            db.add(default_fund)
            db.commit()
            db.refresh(default_fund)
        fund_id = default_fund.id
    else:
        # Verify fund exists
        fund = db.query(Fund).filter(Fund.id == fund_id).first()
        if not fund:
            raise HTTPException(status_code=404, detail=f"Fund with id {fund_id} not found")

    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Error saving file")

    # Create document record
    document = Document(
        fund_id=fund_id,
        file_name=file.filename,
        file_path=file_path,
        parsing_status="pending"
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Start Celery background processing
    try:
        task = process_document_task.delay(document.id, fund_id, file_path)
        task_id = task.id
        logger.info(f"Started Celery task {task_id} for document {document.id}")
    except Exception as e:
        logger.error(f"Error starting Celery task: {e}")
        # Fallback: mark as pending and user can retry
        task_id = None

    return DocumentUploadResponse(
        document_id=document.id,
        task_id=task_id,
        status="pending",
        message="Document uploaded successfully. Processing started in background."
    )


@router.get("/{document_id}/status", response_model=DocumentStatus)
async def get_document_status(document_id: int, db: Session = Depends(get_db)):
    """Get document parsing status"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentStatus(
        document_id=document.id,
        status=document.parsing_status,
        error_message=document.error_message
    )


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.get("/", response_model=List[DocumentSchema])
async def list_documents(
    fund_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all documents"""
    query = db.query(Document)
    
    if fund_id:
        query = query.filter(Document.fund_id == fund_id)
    
    documents = query.offset(skip).limit(limit).all()
    return documents


@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete database record
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}
