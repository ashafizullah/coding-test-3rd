"""
Custom Formula models for user-defined metrics
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base


class CustomFormula(Base):
    """Custom formula model for user-defined metrics"""
    __tablename__ = "custom_formulas"

    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"), nullable=True)  # Null = global formula
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    formula = Column(Text, nullable=False)  # Formula expression (e.g., "total_distributions / pic")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    fund = relationship("Fund", back_populates="custom_formulas")
