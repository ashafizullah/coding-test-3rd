"""
Vector store service using pgvector (PostgreSQL extension)

Stores document embeddings for semantic search and RAG.
"""
from typing import List, Dict, Any, Optional
import numpy as np
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class VectorStore:
    """pgvector-based vector store for document embeddings"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.embeddings = self._initialize_embeddings()
        self._ensure_extension()
    
    def _initialize_embeddings(self):
        """Initialize embedding model"""
        if settings.OPENAI_API_KEY:
            return OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            # Fallback to local embeddings
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
    
    def _ensure_extension(self):
        """
        Ensure pgvector extension is enabled and table exists
        """
        try:
            # Enable pgvector extension
            self.db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension ensured")

            # Create embeddings table
            # Dimension: 1536 for OpenAI, 384 for sentence-transformers/MiniLM
            dimension = 1536 if settings.OPENAI_API_KEY else 384

            # Drop index first if exists (for schema updates)
            self.db.execute(text("DROP INDEX IF EXISTS document_embeddings_embedding_idx"))

            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id SERIAL PRIMARY KEY,
                document_id INTEGER,
                fund_id INTEGER,
                content TEXT NOT NULL,
                embedding vector({dimension}),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            self.db.execute(text(create_table_sql))

            # Create index for fast vector search
            # Note: ivfflat requires some data before creating index, so we check first
            count_result = self.db.execute(text("SELECT COUNT(*) FROM document_embeddings"))
            count = count_result.scalar()

            if count > 100:  # Only create index if we have enough data
                create_index_sql = f"""
                CREATE INDEX IF NOT EXISTS document_embeddings_embedding_idx
                ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
                """
                self.db.execute(text(create_index_sql))
                logger.info("Created ivfflat index for vector search")
            else:
                logger.info(f"Skipping index creation (only {count} rows, need >100 for ivfflat)")

            self.db.commit()
            logger.info(f"Vector store initialized with dimension {dimension}")

        except Exception as e:
            logger.error(f"Error ensuring pgvector extension: {e}")
            self.db.rollback()
            # Don't raise - allow system to continue without vector search
    
    def add_document(self, content: str, metadata: Dict[str, Any]):
        """
        Add a document to the vector store.

        Args:
            content: Document text content
            metadata: Document metadata (document_id, fund_id, page, etc.)
        """
        try:
            # Generate embedding (synchronous call)
            embedding = self._get_embedding(content)
            embedding_list = embedding.tolist()

            # Convert metadata to JSON string
            metadata_json = json.dumps(metadata)

            # Insert into database
            # Use parameterized query with proper type casting
            insert_sql = text("""
                INSERT INTO document_embeddings (document_id, fund_id, content, embedding, metadata)
                VALUES (:document_id, :fund_id, :content, :embedding, :metadata)
                RETURNING id
            """)

            # Convert embedding to pgvector format string
            embedding_str = '[' + ','.join(map(str, embedding_list)) + ']'

            result = self.db.execute(insert_sql, {
                "document_id": metadata.get("document_id"),
                "fund_id": metadata.get("fund_id"),
                "content": content,
                "embedding": embedding_str,
                "metadata": metadata_json
            })

            doc_id = result.scalar()
            self.db.commit()

            logger.debug(f"Added document chunk to vector store (id={doc_id})")
            return doc_id

        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
            self.db.rollback()
            raise
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using cosine similarity.

        Args:
            query: Search query
            k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"fund_id": 1})

        Returns:
            List of similar documents with scores
        """
        try:
            # Generate query embedding
            query_embedding = self._get_embedding(query)
            embedding_list = query_embedding.tolist()

            # Build query with optional filters
            where_clause = ""
            params = {
                "k": k
            }

            if filter_metadata:
                conditions = []
                for key, value in filter_metadata.items():
                    if key in ["document_id", "fund_id"] and value is not None:
                        param_name = f"filter_{key}"
                        conditions.append(f"{key} = :{param_name}")
                        params[param_name] = value

                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)

            # Search using cosine distance (<=> operator)
            # Note: 1 - distance gives similarity score (higher = more similar)
            # Convert embedding to pgvector format string
            embedding_str = '[' + ','.join(map(str, embedding_list)) + ']'

            search_sql = text(f"""
                SELECT
                    id,
                    document_id,
                    fund_id,
                    content,
                    metadata,
                    1 - (embedding <=> :query_embedding) as similarity_score
                FROM document_embeddings
                {where_clause}
                ORDER BY embedding <=> :query_embedding
                LIMIT :k
            """)

            params["query_embedding"] = embedding_str

            result = self.db.execute(search_sql, params)

            # Format results
            results = []
            for row in result:
                results.append({
                    "id": row[0],
                    "document_id": row[1],
                    "fund_id": row[2],
                    "content": row[3],
                    "metadata": row[4],
                    "score": float(row[5])
                })

            logger.info(f"Found {len(results)} similar documents for query: {query[:50]}...")
            return results

        except Exception as e:
            logger.error(f"Error in similarity search: {e}", exc_info=True)
            return []

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.

        Args:
            text: Input text

        Returns:
            Numpy array of embedding vector
        """
        try:
            # Truncate text if too long (model limits)
            max_length = 8000  # Conservative limit
            if len(text) > max_length:
                text = text[:max_length]
                logger.warning(f"Text truncated to {max_length} characters for embedding")

            # Generate embedding
            if hasattr(self.embeddings, 'embed_query'):
                embedding = self.embeddings.embed_query(text)
            else:
                embedding = self.embeddings.encode(text)

            return np.array(embedding, dtype=np.float32)

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def clear(self, fund_id: Optional[int] = None):
        """
        Clear the vector store
        
        TODO: Implement this method
        - Delete all embeddings (or filter by fund_id)
        """
        try:
            if fund_id:
                delete_sql = text("DELETE FROM document_embeddings WHERE fund_id = :fund_id")
                self.db.execute(delete_sql, {"fund_id": fund_id})
            else:
                delete_sql = text("DELETE FROM document_embeddings")
                self.db.execute(delete_sql)

            self.db.commit()
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            self.db.rollback()
