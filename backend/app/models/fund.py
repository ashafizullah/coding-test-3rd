"""
Fund database model
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base


class Fund(Base):
    """Fund model"""

    __tablename__ = "funds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    gp_name = Column(String(255))
    fund_type = Column(String(100))
    vintage_year = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    capital_calls = relationship("CapitalCall", back_populates="fund", cascade="all, delete-orphan")
    distributions = relationship("Distribution", back_populates="fund", cascade="all, delete-orphan")
    adjustments = relationship("Adjustment", back_populates="fund", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="fund", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="fund", cascade="all, delete-orphan")
    custom_formulas = relationship("CustomFormula", back_populates="fund", cascade="all, delete-orphan")
