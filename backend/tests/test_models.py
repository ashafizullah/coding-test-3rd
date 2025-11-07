"""
Unit tests for database models
"""
import pytest
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.models.fund import Fund
from app.models.transaction import CapitalCall, Distribution, Adjustment
from app.models.document import Document
from app.models.conversation import Conversation, ConversationMessage
from app.models.custom_formula import CustomFormula


class TestFundModel:
    """Test suite for Fund model"""

    def test_create_fund(self, db_session):
        """Test creating a fund"""
        fund = Fund(
            name="Test Fund",
            gp_name="Test GP",
            fund_type="Venture Capital",
            vintage_year=2023,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(fund)
        db_session.commit()

        assert fund.id is not None
        assert fund.name == "Test Fund"
        assert fund.vintage_year == 2023

    def test_fund_relationships(self, db_session, sample_fund, sample_capital_calls):
        """Test fund relationships"""
        # Refresh to load relationships
        db_session.refresh(sample_fund)

        assert len(sample_fund.capital_calls) == 3
        assert sample_fund.capital_calls[0].fund_id == sample_fund.id


class TestCapitalCallModel:
    """Test suite for CapitalCall model"""

    def test_create_capital_call(self, db_session, sample_fund):
        """Test creating a capital call"""
        call = CapitalCall(
            fund_id=sample_fund.id,
            call_date=date(2023, 1, 15),
            call_type="Initial",
            amount=Decimal("1000000.00"),
            description="Test capital call",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(call)
        db_session.commit()

        assert call.id is not None
        assert call.amount == Decimal("1000000.00")

    def test_capital_call_requires_fund(self, db_session):
        """Test that capital call requires a fund"""
        call = CapitalCall(
            fund_id=9999,  # Non-existent fund
            call_date=date(2023, 1, 15),
            amount=Decimal("1000000.00"),
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(call)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestDistributionModel:
    """Test suite for Distribution model"""

    def test_create_distribution(self, db_session, sample_fund):
        """Test creating a distribution"""
        dist = Distribution(
            fund_id=sample_fund.id,
            distribution_date=date(2023, 6, 15),
            distribution_type="Dividend",
            is_recallable=False,
            amount=Decimal("500000.00"),
            description="Test distribution",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(dist)
        db_session.commit()

        assert dist.id is not None
        assert dist.amount == Decimal("500000.00")
        assert dist.is_recallable is False

    def test_distribution_recallable_default(self, db_session, sample_fund):
        """Test that is_recallable defaults to False"""
        dist = Distribution(
            fund_id=sample_fund.id,
            distribution_date=date(2023, 6, 15),
            amount=Decimal("500000.00"),
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(dist)
        db_session.commit()

        assert dist.is_recallable is False


class TestAdjustmentModel:
    """Test suite for Adjustment model"""

    def test_create_adjustment(self, db_session, sample_fund):
        """Test creating an adjustment"""
        adj = Adjustment(
            fund_id=sample_fund.id,
            adjustment_date=date(2023, 3, 10),
            adjustment_type="Expense",
            category="Management Fee",
            amount=Decimal("50000.00"),
            is_contribution_adjustment=False,
            description="Test adjustment",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(adj)
        db_session.commit()

        assert adj.id is not None
        assert adj.amount == Decimal("50000.00")


class TestDocumentModel:
    """Test suite for Document model"""

    def test_create_document(self, db_session, sample_fund):
        """Test creating a document"""
        doc = Document(
            fund_id=sample_fund.id,
            file_name="test.pdf",
            file_path="/uploads/test.pdf",
            upload_date=datetime.now(timezone.utc),
            parsing_status="pending"
        )
        db_session.add(doc)
        db_session.commit()

        assert doc.id is not None
        assert doc.parsing_status == "pending"

    def test_document_status_update(self, db_session, sample_document):
        """Test updating document status"""
        sample_document.parsing_status = "completed"
        db_session.commit()

        db_session.refresh(sample_document)
        assert sample_document.parsing_status == "completed"


class TestConversationModel:
    """Test suite for Conversation model"""

    def test_create_conversation(self, db_session, sample_fund):
        """Test creating a conversation"""
        conv = Conversation(
            conversation_id="test-conv-123",
            fund_id=sample_fund.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(conv)
        db_session.commit()

        assert conv.id is not None
        assert conv.conversation_id == "test-conv-123"

    def test_conversation_cascade_delete(self, db_session, sample_conversation):
        """Test that deleting a conversation deletes its messages"""
        conversation_id = sample_conversation.id

        # Count messages before delete
        message_count = db_session.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).count()
        assert message_count == 2

        # Delete conversation
        db_session.delete(sample_conversation)
        db_session.commit()

        # Check messages are deleted
        message_count = db_session.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).count()
        assert message_count == 0

    def test_conversation_unique_id(self, db_session, sample_fund):
        """Test that conversation_id must be unique"""
        conv1 = Conversation(
            conversation_id="duplicate-id",
            fund_id=sample_fund.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(conv1)
        db_session.commit()

        conv2 = Conversation(
            conversation_id="duplicate-id",
            fund_id=sample_fund.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(conv2)

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestConversationMessageModel:
    """Test suite for ConversationMessage model"""

    def test_create_message(self, db_session, sample_conversation):
        """Test creating a conversation message"""
        message = ConversationMessage(
            conversation_id=sample_conversation.id,
            role="user",
            content="Test message",
            timestamp=datetime.now(timezone.utc)
        )
        db_session.add(message)
        db_session.commit()

        assert message.id is not None
        assert message.role == "user"
        assert message.content == "Test message"

    def test_message_with_metadata(self, db_session, sample_conversation):
        """Test creating a message with metadata"""
        message = ConversationMessage(
            conversation_id=sample_conversation.id,
            role="assistant",
            content="Response with metadata",
            message_metadata={"sources": ["doc1", "doc2"], "metrics": {"dpi": 0.5}},
            timestamp=datetime.now(timezone.utc)
        )
        db_session.add(message)
        db_session.commit()

        assert message.message_metadata is not None
        assert "sources" in message.message_metadata
        assert "metrics" in message.message_metadata


class TestCustomFormulaModel:
    """Test suite for CustomFormula model"""

    def test_create_custom_formula(self, db_session, sample_fund):
        """Test creating a custom formula"""
        formula = CustomFormula(
            fund_id=sample_fund.id,
            name="Custom Metric",
            description="Test custom metric",
            formula="total_distributions / pic",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(formula)
        db_session.commit()

        assert formula.id is not None
        assert formula.name == "Custom Metric"
        assert formula.is_active is True

    def test_global_custom_formula(self, db_session):
        """Test creating a global custom formula (no fund_id)"""
        formula = CustomFormula(
            fund_id=None,  # Global formula
            name="Global Metric",
            description="Global custom metric",
            formula="nav / pic",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(formula)
        db_session.commit()

        assert formula.id is not None
        assert formula.fund_id is None

    def test_custom_formula_is_active_default(self, db_session, sample_fund):
        """Test that is_active defaults to True"""
        formula = CustomFormula(
            fund_id=sample_fund.id,
            name="Test Formula",
            formula="nav + pic",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(formula)
        db_session.commit()

        assert formula.is_active is True
