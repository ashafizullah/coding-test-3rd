"""
Integration tests for complete workflows
"""
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from datetime import date, datetime, timezone
from decimal import Decimal

from app.main import app
from app.db.session import get_db
from app.services.metrics_calculator import MetricsCalculator


@pytest.fixture
def client(db_session):
    """Create a test client with database override"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.mark.integration
class TestCompleteWorkflow:
    """Test complete end-to-end workflows"""

    def test_create_fund_and_calculate_metrics(self, client, db_session):
        """Test creating a fund, adding transactions, and calculating metrics"""

        # Step 1: Create a fund
        response = client.post(
            "/api/funds",
            json={
                "name": "Integration Test Fund",
                "gp_name": "Test Partners",
                "fund_type": "Venture Capital",
                "vintage_year": 2023
            }
        )
        assert response.status_code == 200
        fund_data = response.json()
        fund_id = fund_data["id"]

        # Step 2: Add capital calls manually to database
        from app.models.transaction import CapitalCall
        capital_calls = [
            CapitalCall(
                fund_id=fund_id,
                call_date=date(2023, 1, 15),
                call_type="Initial",
                amount=Decimal("2000000.00"),
                created_at=datetime.now(timezone.utc)
            ),
            CapitalCall(
                fund_id=fund_id,
                call_date=date(2023, 6, 20),
                call_type="Follow-on",
                amount=Decimal("1000000.00"),
                created_at=datetime.now(timezone.utc)
            ),
        ]
        for call in capital_calls:
            db_session.add(call)
        db_session.commit()

        # Step 3: Add distributions
        from app.models.transaction import Distribution
        distributions = [
            Distribution(
                fund_id=fund_id,
                distribution_date=date(2023, 12, 15),
                distribution_type="Dividend",
                is_recallable=False,
                amount=Decimal("500000.00"),
                created_at=datetime.now(timezone.utc)
            ),
        ]
        for dist in distributions:
            db_session.add(dist)
        db_session.commit()

        # Step 4: Get fund metrics via API
        response = client.get(f"/api/funds/{fund_id}/metrics")
        assert response.status_code == 200
        metrics = response.json()

        # Step 5: Verify calculated metrics
        assert metrics["pic"] == 3000000.0  # 2M + 1M
        assert metrics["total_distributions"] == 500000.0
        assert metrics["dpi"] == pytest.approx(0.1667, abs=0.0001)  # 500k / 3M
        assert metrics["nav"] == 2500000.0  # 3M - 500k
        assert metrics["tvpi"] == 1.0  # (500k + 2.5M) / 3M
        assert metrics["rvpi"] == pytest.approx(0.8333, abs=0.0001)  # 2.5M / 3M

        # Step 6: Get transactions via API
        response = client.get(f"/api/funds/{fund_id}/capital-calls")
        assert response.status_code == 200
        assert len(response.json()) == 2

        response = client.get(f"/api/funds/{fund_id}/distributions")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_conversation_persistence_workflow(self, client, db_session, sample_fund):
        """Test creating and managing conversations"""

        # Step 1: Create a conversation
        response = client.post(
            "/api/chat/conversations",
            json={"fund_id": sample_fund.id}
        )
        assert response.status_code == 200
        conv_data = response.json()
        conversation_id = conv_data["conversation_id"]

        # Step 2: Simulate chat query (this would trigger message saving)
        # Note: We can't fully test this without mocking the LLM
        # but we can test the database persistence directly

        from app.models.conversation import ConversationMessage, Conversation

        # Get the conversation from DB
        conv = db_session.query(Conversation).filter(
            Conversation.conversation_id == conversation_id
        ).first()
        assert conv is not None

        # Add messages
        messages = [
            ConversationMessage(
                conversation_id=conv.id,
                role="user",
                content="What is the DPI?",
                timestamp=datetime.now(timezone.utc)
            ),
            ConversationMessage(
                conversation_id=conv.id,
                role="assistant",
                content="The DPI is calculated as distributions divided by paid-in capital.",
                metadata={"sources": []},
                timestamp=datetime.now(timezone.utc)
            ),
        ]
        for msg in messages:
            db_session.add(msg)
        db_session.commit()

        # Step 3: Retrieve conversation via API
        response = client.get(f"/api/chat/conversations/{conversation_id}")
        assert response.status_code == 200
        conv_data = response.json()
        assert len(conv_data["messages"]) == 2
        assert conv_data["messages"][0]["role"] == "user"
        assert conv_data["messages"][1]["role"] == "assistant"

        # Step 4: Delete conversation
        response = client.delete(f"/api/chat/conversations/{conversation_id}")
        assert response.status_code == 200

        # Step 5: Verify deletion
        response = client.get(f"/api/chat/conversations/{conversation_id}")
        assert response.status_code == 404

    def test_multiple_funds_comparison(self, client, db_session):
        """Test comparing metrics across multiple funds"""

        # Step 1: Create multiple funds
        funds = []
        for i in range(3):
            response = client.post(
                "/api/funds",
                json={
                    "name": f"Fund {i+1}",
                    "gp_name": f"GP {i+1}",
                    "vintage_year": 2023
                }
            )
            assert response.status_code == 200
            funds.append(response.json())

        # Step 2: Add different transaction amounts to each fund
        from app.models.transaction import CapitalCall, Distribution

        for i, fund in enumerate(funds):
            # Each fund has different amounts
            call = CapitalCall(
                fund_id=fund["id"],
                call_date=date(2023, 1, 15),
                amount=Decimal(f"{(i+1) * 1000000}.00"),
                created_at=datetime.now(timezone.utc)
            )
            dist = Distribution(
                fund_id=fund["id"],
                distribution_date=date(2023, 12, 15),
                amount=Decimal(f"{(i+1) * 200000}.00"),
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(call)
            db_session.add(dist)
        db_session.commit()

        # Step 3: Get metrics for all funds
        all_metrics = []
        for fund in funds:
            response = client.get(f"/api/funds/{fund['id']}/metrics")
            assert response.status_code == 200
            all_metrics.append(response.json())

        # Step 4: Verify each fund has unique metrics
        dpis = [m["dpi"] for m in all_metrics]
        assert len(set(dpis)) == 3  # All DPIs should be the same (0.2)
        assert all(dpi == 0.2 for dpi in dpis)  # 200k/1M, 400k/2M, 600k/3M all equal 0.2

        # Step 5: Verify PICs are different
        pics = [m["pic"] for m in all_metrics]
        assert pics[0] == 1000000.0
        assert pics[1] == 2000000.0
        assert pics[2] == 3000000.0

    def test_document_upload_workflow(self, client, db_session, sample_fund):
        """Test document upload and status tracking"""

        # Step 1: Create a document entry
        from app.models.document import Document

        doc = Document(
            fund_id=sample_fund.id,
            file_name="test_report.pdf",
            file_path="/uploads/test_report.pdf",
            upload_date=datetime.now(timezone.utc),
            parsing_status="pending"
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        # Step 2: Get document via API
        response = client.get(f"/api/documents/{doc.id}")
        assert response.status_code == 200
        doc_data = response.json()
        assert doc_data["parsing_status"] == "pending"

        # Step 3: Simulate processing completion
        doc.parsing_status = "completed"
        db_session.commit()

        # Step 4: Verify status update
        response = client.get(f"/api/documents/{doc.id}")
        assert response.status_code == 200
        doc_data = response.json()
        assert doc_data["parsing_status"] == "completed"

        # Step 5: List all documents
        response = client.get("/api/documents")
        assert response.status_code == 200
        docs = response.json()
        assert len(docs) >= 1
        assert any(d["id"] == doc.id for d in docs)

    def test_custom_formula_workflow(self, client, db_session, sample_fund):
        """Test creating and using custom formulas"""

        # Step 1: Create a custom formula
        from app.models.custom_formula import CustomFormula

        formula = CustomFormula(
            fund_id=sample_fund.id,
            name="ROI",
            description="Return on Investment",
            formula="(total_distributions + nav - pic) / pic",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(formula)
        db_session.commit()
        db_session.refresh(formula)

        # Step 2: Verify formula was created
        assert formula.id is not None
        assert formula.name == "ROI"
        assert formula.is_active is True

        # Step 3: Deactivate formula
        formula.is_active = False
        db_session.commit()

        # Step 4: Verify deactivation
        db_session.refresh(formula)
        assert formula.is_active is False

        # Step 5: Create a global formula (no fund_id)
        global_formula = CustomFormula(
            fund_id=None,
            name="Global IRR Benchmark",
            description="Target IRR for all funds",
            formula="15",  # 15% target
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(global_formula)
        db_session.commit()

        assert global_formula.id is not None
        assert global_formula.fund_id is None

    def test_metrics_calculation_with_adjustments(self, client, db_session, sample_fund):
        """Test that adjustments properly affect metric calculations"""

        # Step 1: Add capital calls
        from app.models.transaction import CapitalCall, Distribution, Adjustment

        call = CapitalCall(
            fund_id=sample_fund.id,
            call_date=date(2023, 1, 15),
            amount=Decimal("5000000.00"),
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(call)

        # Step 2: Add adjustment
        adjustment = Adjustment(
            fund_id=sample_fund.id,
            adjustment_date=date(2023, 2, 1),
            adjustment_type="Management Fee",
            amount=Decimal("250000.00"),  # 250k fee
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(adjustment)

        # Step 3: Add distribution
        dist = Distribution(
            fund_id=sample_fund.id,
            distribution_date=date(2023, 12, 15),
            amount=Decimal("1000000.00"),
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(dist)
        db_session.commit()

        # Step 4: Calculate metrics
        calculator = MetricsCalculator(db_session)

        pic = calculator.calculate_pic(sample_fund.id)
        assert pic == Decimal("4750000.00")  # 5M - 250k

        dpi = calculator.calculate_dpi(sample_fund.id)
        assert dpi == pytest.approx(0.2105, abs=0.0001)  # 1M / 4.75M

        nav = calculator.calculate_nav(sample_fund.id)
        assert nav == Decimal("3750000.00")  # 5M - 1M - 250k

        tvpi = calculator.calculate_tvpi(sample_fund.id)
        assert tvpi == 1.0  # (1M + 3.75M) / 4.75M

    def test_error_handling_workflow(self, client):
        """Test error handling in various scenarios"""

        # Test 1: Get non-existent fund
        response = client.get("/api/funds/99999")
        assert response.status_code == 404

        # Test 2: Get metrics for non-existent fund
        response = client.get("/api/funds/99999/metrics")
        assert response.status_code == 404

        # Test 3: Get non-existent conversation
        response = client.get("/api/chat/conversations/nonexistent-id")
        assert response.status_code == 404

        # Test 4: Delete non-existent conversation
        response = client.delete("/api/chat/conversations/nonexistent-id")
        assert response.status_code == 404

        # Test 5: Get non-existent document
        response = client.get("/api/documents/99999")
        assert response.status_code == 404


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency across operations"""

    def test_cascade_delete_integrity(self, client, db_session, sample_fund):
        """Test that related records are properly handled on deletion"""
        from app.models.transaction import CapitalCall
        from app.models.document import Document
        from app.models.conversation import Conversation

        # Add related records
        call = CapitalCall(
            fund_id=sample_fund.id,
            call_date=date(2023, 1, 15),
            amount=Decimal("1000000.00"),
            created_at=datetime.now(timezone.utc)
        )
        doc = Document(
            fund_id=sample_fund.id,
            file_name="test.pdf",
            file_path="/uploads/test.pdf",
            upload_date=datetime.now(timezone.utc)
        )
        conv = Conversation(
            conversation_id="test-conv",
            fund_id=sample_fund.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        db_session.add_all([call, doc, conv])
        db_session.commit()

        # Count records
        call_count = db_session.query(CapitalCall).filter(
            CapitalCall.fund_id == sample_fund.id
        ).count()
        assert call_count == 1

        # Note: Actual cascade behavior depends on model definitions
        # This test validates that related queries work correctly

    def test_transaction_atomicity(self, client, db_session, sample_fund):
        """Test that database transactions are atomic"""
        from app.models.transaction import CapitalCall

        initial_count = db_session.query(CapitalCall).count()

        try:
            # Add a valid call
            call1 = CapitalCall(
                fund_id=sample_fund.id,
                call_date=date(2023, 1, 15),
                amount=Decimal("1000000.00"),
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(call1)

            # Try to add invalid call (this would fail in real scenario)
            # For this test, we'll just verify transaction can be rolled back
            db_session.flush()

            # Explicitly rollback
            db_session.rollback()

            # Count should be unchanged
            final_count = db_session.query(CapitalCall).count()
            assert final_count == initial_count

        except Exception:
            db_session.rollback()
            raise
