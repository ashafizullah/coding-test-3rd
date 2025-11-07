"""
Test configuration and fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone, date
from decimal import Decimal

from app.db.base import Base
from app.models.fund import Fund
from app.models.transaction import CapitalCall, Distribution, Adjustment
from app.models.document import Document
from app.models.conversation import Conversation, ConversationMessage
from app.models.custom_formula import CustomFormula


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Use in-memory SQLite database for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_fund(db_session):
    """Create a sample fund for testing"""
    fund = Fund(
        name="Test Venture Fund I",
        gp_name="Test Ventures",
        fund_type="Venture Capital",
        vintage_year=2020,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(fund)
    db_session.commit()
    db_session.refresh(fund)
    return fund


@pytest.fixture
def sample_capital_calls(db_session, sample_fund):
    """Create sample capital calls"""
    calls = [
        CapitalCall(
            fund_id=sample_fund.id,
            call_date=date(2020, 1, 15),
            call_type="Initial Closing",
            amount=Decimal("1000000.00"),
            description="First capital call",
            created_at=datetime.now(timezone.utc)
        ),
        CapitalCall(
            fund_id=sample_fund.id,
            call_date=date(2020, 6, 20),
            call_type="Follow-on",
            amount=Decimal("500000.00"),
            description="Second capital call",
            created_at=datetime.now(timezone.utc)
        ),
        CapitalCall(
            fund_id=sample_fund.id,
            call_date=date(2021, 3, 10),
            call_type="Follow-on",
            amount=Decimal("750000.00"),
            description="Third capital call",
            created_at=datetime.now(timezone.utc)
        ),
    ]

    for call in calls:
        db_session.add(call)

    db_session.commit()
    return calls


@pytest.fixture
def sample_distributions(db_session, sample_fund):
    """Create sample distributions"""
    distributions = [
        Distribution(
            fund_id=sample_fund.id,
            distribution_date=date(2021, 12, 15),
            distribution_type="Dividend",
            is_recallable=False,
            amount=Decimal("200000.00"),
            description="First distribution",
            created_at=datetime.now(timezone.utc)
        ),
        Distribution(
            fund_id=sample_fund.id,
            distribution_date=date(2022, 6, 30),
            distribution_type="Capital Return",
            is_recallable=False,
            amount=Decimal("450000.00"),
            description="Second distribution",
            created_at=datetime.now(timezone.utc)
        ),
        Distribution(
            fund_id=sample_fund.id,
            distribution_date=date(2023, 1, 20),
            distribution_type="Dividend",
            is_recallable=True,
            amount=Decimal("300000.00"),
            description="Third distribution (recallable)",
            created_at=datetime.now(timezone.utc)
        ),
    ]

    for dist in distributions:
        db_session.add(dist)

    db_session.commit()
    return distributions


@pytest.fixture
def sample_adjustments(db_session, sample_fund):
    """Create sample adjustments"""
    adjustments = [
        Adjustment(
            fund_id=sample_fund.id,
            adjustment_date=date(2020, 7, 1),
            adjustment_type="Expense Allocation",
            category="Management Fee",
            amount=Decimal("50000.00"),
            is_contribution_adjustment=False,
            description="Management fee adjustment",
            created_at=datetime.now(timezone.utc)
        ),
    ]

    for adj in adjustments:
        db_session.add(adj)

    db_session.commit()
    return adjustments


@pytest.fixture
def sample_document(db_session, sample_fund):
    """Create a sample document"""
    document = Document(
        fund_id=sample_fund.id,
        file_name="test_report.pdf",
        file_path="/uploads/test_report.pdf",
        upload_date=datetime.now(timezone.utc),
        parsing_status="completed"
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


@pytest.fixture
def sample_conversation(db_session, sample_fund):
    """Create a sample conversation with messages"""
    conversation = Conversation(
        conversation_id="test-conversation-123",
        fund_id=sample_fund.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)

    # Add some messages
    messages = [
        ConversationMessage(
            conversation_id=conversation.id,
            role="user",
            content="What is the DPI?",
            timestamp=datetime.now(timezone.utc)
        ),
        ConversationMessage(
            conversation_id=conversation.id,
            role="assistant",
            content="The DPI is 0.42x",
            metadata={"sources": [], "metrics": {"dpi": 0.42}},
            timestamp=datetime.now(timezone.utc)
        ),
    ]

    for message in messages:
        db_session.add(message)

    db_session.commit()
    return conversation


@pytest.fixture
def sample_custom_formula(db_session, sample_fund):
    """Create a sample custom formula"""
    formula = CustomFormula(
        fund_id=sample_fund.id,
        name="Custom ROI",
        description="Custom return on investment calculation",
        formula="(total_distributions + nav) / pic",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(formula)
    db_session.commit()
    db_session.refresh(formula)
    return formula


@pytest.fixture
def complete_fund_with_transactions(db_session, sample_fund, sample_capital_calls, sample_distributions, sample_adjustments):
    """Fixture that provides a fund with all transaction types"""
    return {
        "fund": sample_fund,
        "capital_calls": sample_capital_calls,
        "distributions": sample_distributions,
        "adjustments": sample_adjustments
    }
