"""
Document processing service using pdfplumber

Extracts tables and text from PDF documents for fund performance analysis.
"""
from typing import Dict, List, Any, Optional
import pdfplumber
import logging
import re
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.table_parser import TableParser
from app.services.vector_store import VectorStore
from app.models.transaction import CapitalCall, Distribution, Adjustment
from app.models.document import Document as DocumentModel

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process PDF documents and extract structured data"""

    def __init__(self, db: Session):
        self.db = db
        self.table_parser = TableParser()
        self.vector_store = VectorStore(db)

    async def process_document(self, file_path: str, document_id: int, fund_id: int) -> Dict[str, Any]:
        """
        Process a PDF document

        Workflow:
        1. Extract tables from PDF
        2. Classify and parse tables
        3. Save tables to database
        4. Extract text content
        5. Chunk and vectorize text
        6. Store in vector database

        Args:
            file_path: Path to the PDF file
            document_id: Database document ID
            fund_id: Fund ID

        Returns:
            Processing result with statistics
        """
        stats = {
            'capital_calls': 0,
            'distributions': 0,
            'adjustments': 0,
            'text_chunks': 0,
            'tables_found': 0,
            'pages_processed': 0,
            'errors': []
        }

        try:
            logger.info(f"Starting document processing: {file_path}")

            # Step 1: Extract tables from PDF
            tables = self.table_parser.extract_tables_from_pdf(file_path)
            stats['tables_found'] = len(tables)

            # Step 2: Process each table
            for table_info in tables:
                try:
                    # Classify table type
                    table_type = self.table_parser.classify_table_type(table_info)

                    if not table_type:
                        logger.warning(f"Could not classify table on page {table_info['page']}")
                        continue

                    # Parse table based on type
                    if table_type == 'capital_calls':
                        parsed_data = self.table_parser.parse_capital_call_table(table_info)
                        validated_data = self.table_parser.validate_and_clean_data(parsed_data, table_type)
                        self._save_capital_calls(validated_data, fund_id)
                        stats['capital_calls'] += len(validated_data)

                    elif table_type == 'distributions':
                        parsed_data = self.table_parser.parse_distribution_table(table_info)
                        validated_data = self.table_parser.validate_and_clean_data(parsed_data, table_type)
                        self._save_distributions(validated_data, fund_id)
                        stats['distributions'] += len(validated_data)

                    elif table_type == 'adjustments':
                        parsed_data = self.table_parser.parse_adjustment_table(table_info)
                        validated_data = self.table_parser.validate_and_clean_data(parsed_data, table_type)
                        self._save_adjustments(validated_data, fund_id)
                        stats['adjustments'] += len(validated_data)

                except Exception as e:
                    error_msg = f"Error processing table on page {table_info.get('page')}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)

            # Step 2.5: Fallback to LLM-based text extraction if no tables found
            if stats['tables_found'] == 0 or (stats['capital_calls'] == 0 and stats['distributions'] == 0):
                logger.info("No structured tables found, attempting LLM-based text extraction")
                try:
                    llm_data = self.table_parser.extract_data_from_text(file_path)
                    llm_calls_count = 0
                    llm_dists_count = 0

                    # Save capital calls
                    if llm_data.get('capital_calls'):
                        validated_calls = self.table_parser.validate_and_clean_data(
                            llm_data['capital_calls'], 'capital_calls'
                        )
                        self._save_capital_calls(validated_calls, fund_id)
                        stats['capital_calls'] += len(validated_calls)
                        llm_calls_count = len(validated_calls)

                    # Save distributions
                    if llm_data.get('distributions'):
                        validated_dists = self.table_parser.validate_and_clean_data(
                            llm_data['distributions'], 'distributions'
                        )
                        self._save_distributions(validated_dists, fund_id)
                        stats['distributions'] += len(validated_dists)
                        llm_dists_count = len(validated_dists)

                    logger.info(f"LLM extraction completed: {llm_calls_count} capital calls, {llm_dists_count} distributions")

                except Exception as e:
                    error_msg = f"Error in LLM-based text extraction: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)

            # Step 3: Extract text content for RAG
            text_content = self._extract_text_content(file_path)
            stats['pages_processed'] = len(text_content)

            # Step 4: Chunk text
            chunks = self._chunk_text(text_content)
            stats['text_chunks'] = len(chunks)

            # Step 5: Store chunks in vector database
            if chunks:
                for chunk in chunks:
                    self.vector_store.add_document(
                        content=chunk['text'],
                        metadata={
                            'document_id': document_id,
                            'fund_id': fund_id,
                            'page': chunk['page'],
                            'chunk_index': chunk['chunk_index'],
                            'source': file_path
                        }
                    )

            # Step 6: Update document status
            self._update_document_status(document_id, 'completed', None)

            logger.info(f"Document processing completed: {stats}")
            return {
                'success': True,
                'stats': stats
            }

        except Exception as e:
            error_msg = f"Fatal error processing document {file_path}: {e}"
            logger.error(error_msg, exc_info=True)
            stats['errors'].append(error_msg)

            # Update document status to failed
            self._update_document_status(document_id, 'failed', error_msg)

            return {
                'success': False,
                'stats': stats,
                'error': error_msg
            }

    def _extract_text_content(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text content from PDF.

        Args:
            file_path: Path to PDF file

        Returns:
            List of dictionaries with page text and metadata
        """
        text_content = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text
                    text = page.extract_text()

                    if text and text.strip():
                        text_content.append({
                            'page': page_num,
                            'text': text,
                            'total_pages': len(pdf.pages)
                        })

            logger.info(f"Extracted text from {len(text_content)} pages")
            return text_content

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise

    def _chunk_text(self, text_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk text content for vector storage.

        Uses intelligent chunking with:
        - Sentence boundary preservation
        - Context overlap
        - Metadata preservation

        Args:
            text_content: List of text content with metadata

        Returns:
            List of text chunks with metadata
        """
        chunks = []
        chunk_size = settings.CHUNK_SIZE
        chunk_overlap = settings.CHUNK_OVERLAP

        for page_data in text_content:
            text = page_data['text']
            page_num = page_data['page']

            # Split text into sentences
            sentences = self._split_into_sentences(text)

            # Create chunks from sentences
            current_chunk = []
            current_length = 0
            chunk_index = 0

            for sentence in sentences:
                sentence_length = len(sentence)

                # If adding this sentence exceeds chunk size, save current chunk
                if current_length + sentence_length > chunk_size and current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunks.append({
                        'text': chunk_text,
                        'page': page_num,
                        'chunk_index': chunk_index,
                        'char_count': len(chunk_text)
                    })

                    # Keep last few sentences for overlap
                    overlap_sentences = []
                    overlap_length = 0
                    for sent in reversed(current_chunk):
                        if overlap_length + len(sent) <= chunk_overlap:
                            overlap_sentences.insert(0, sent)
                            overlap_length += len(sent)
                        else:
                            break

                    current_chunk = overlap_sentences
                    current_length = overlap_length
                    chunk_index += 1

                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_length += sentence_length

            # Add remaining text as final chunk
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'page': page_num,
                    'chunk_index': chunk_index,
                    'char_count': len(chunk_text)
                })

        logger.info(f"Created {len(chunks)} text chunks")
        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using simple regex.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with NLP library)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _save_capital_calls(self, capital_calls: List[Dict], fund_id: int):
        """Save capital calls to database"""
        for call_data in capital_calls:
            capital_call = CapitalCall(
                fund_id=fund_id,
                call_date=call_data['call_date'],
                call_type=call_data['call_type'],
                amount=call_data['amount'],
                description=call_data['description']
            )
            self.db.add(capital_call)

        self.db.commit()
        logger.info(f"Saved {len(capital_calls)} capital calls to database")

    def _save_distributions(self, distributions: List[Dict], fund_id: int):
        """Save distributions to database"""
        for dist_data in distributions:
            distribution = Distribution(
                fund_id=fund_id,
                distribution_date=dist_data['distribution_date'],
                distribution_type=dist_data['distribution_type'],
                amount=dist_data['amount'],
                is_recallable=dist_data['is_recallable'],
                description=dist_data['description']
            )
            self.db.add(distribution)

        self.db.commit()
        logger.info(f"Saved {len(distributions)} distributions to database")

    def _save_adjustments(self, adjustments: List[Dict], fund_id: int):
        """Save adjustments to database"""
        for adj_data in adjustments:
            adjustment = Adjustment(
                fund_id=fund_id,
                adjustment_date=adj_data['adjustment_date'],
                adjustment_type=adj_data['adjustment_type'],
                category=adj_data['category'],
                amount=adj_data['amount'],
                is_contribution_adjustment=adj_data['is_contribution_adjustment'],
                description=adj_data['description']
            )
            self.db.add(adjustment)

        self.db.commit()
        logger.info(f"Saved {len(adjustments)} adjustments to database")

    def _update_document_status(self, document_id: int, status: str, error_message: Optional[str]):
        """Update document processing status"""
        try:
            document = self.db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            if document:
                document.parsing_status = status
                document.error_message = error_message
                self.db.commit()
                logger.info(f"Updated document {document_id} status to {status}")
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
            self.db.rollback()
