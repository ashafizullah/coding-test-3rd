"""
Celery tasks for document processing
"""
import logging
from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.document_processor import DocumentProcessor
from app.models.document import Document as DocumentModel

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.document_tasks.process_document_task")
def process_document_task(self, document_id: int, fund_id: int, file_path: str):
    """
    Background task to process a document.

    Args:
        self: Celery task instance (bound)
        document_id: ID of the document in database
        fund_id: ID of the fund
        file_path: Path to the PDF file

    Returns:
        Processing result dictionary
    """
    db = SessionLocal()

    try:
        logger.info(f"Starting document processing task for document {document_id}")

        # Update status to processing
        document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if document:
            document.parsing_status = "processing"
            db.commit()

        # Process document
        processor = DocumentProcessor(db)

        # Note: We use asyncio.run() to run async function in Celery
        import asyncio
        result = asyncio.run(processor.process_document(file_path, document_id, fund_id))

        logger.info(f"Document processing task completed for document {document_id}")
        return result

    except Exception as e:
        logger.error(f"Error in document processing task for document {document_id}: {e}", exc_info=True)

        # Update document status to failed
        try:
            document = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            if document:
                document.parsing_status = "failed"
                document.error_message = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating document status: {db_error}")

        # Re-raise the exception so Celery knows the task failed
        raise

    finally:
        db.close()
