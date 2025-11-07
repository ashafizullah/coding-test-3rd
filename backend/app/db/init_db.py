"""
Database initialization
"""
import logging
from app.db.base import Base
from app.db.session import engine
# Import models to ensure they are registered with SQLAlchemy
from app.models.fund import Fund  # noqa: F401
from app.models.transaction import CapitalCall, Distribution, Adjustment  # noqa: F401
from app.models.document import Document  # noqa: F401

logger = logging.getLogger(__name__)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")
    print("Database tables created successfully!")  # Keep print for docker logs visibility


if __name__ == "__main__":
    init_db()
