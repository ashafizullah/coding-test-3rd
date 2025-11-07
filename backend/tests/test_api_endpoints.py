"""
Unit tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date
from decimal import Decimal

from app.main import app
from app.db.session import get_db


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


class TestFundsEndpoints:
    """Test suite for funds endpoints"""

    def test_create_fund(self, client):
        """Test creating a new fund"""
        response = client.post(
            "/api/funds",
            json={
                "name": "Test Fund",
                "gp_name": "Test GP",
                "fund_type": "Venture Capital",
                "vintage_year": 2023
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Fund"
        assert data["vintage_year"] == 2023

    def test_list_funds(self, client, sample_fund):
        """Test listing all funds"""
        response = client.get("/api/funds")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_fund(self, client, sample_fund):
        """Test getting a specific fund"""
        response = client.get(f"/api/funds/{sample_fund.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_fund.id
        assert data["name"] == sample_fund.name

    def test_get_fund_not_found(self, client):
        """Test getting a non-existent fund"""
        response = client.get("/api/funds/9999")

        assert response.status_code == 404

    def test_get_fund_metrics(self, client, complete_fund_with_transactions):
        """Test getting fund metrics"""
        fund = complete_fund_with_transactions["fund"]

        response = client.get(f"/api/funds/{fund.id}/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "pic" in data
        assert "dpi" in data
        assert "irr" in data
        assert "nav" in data
        assert "tvpi" in data
        assert "rvpi" in data


class TestTransactionsEndpoints:
    """Test suite for transactions endpoints"""

    def test_get_capital_calls(self, client, sample_fund, sample_capital_calls):
        """Test getting capital calls for a fund"""
        response = client.get(f"/api/funds/{sample_fund.id}/capital-calls")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_get_distributions(self, client, sample_fund, sample_distributions):
        """Test getting distributions for a fund"""
        response = client.get(f"/api/funds/{sample_fund.id}/distributions")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_get_adjustments(self, client, sample_fund, sample_adjustments):
        """Test getting adjustments for a fund"""
        response = client.get(f"/api/funds/{sample_fund.id}/adjustments")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1


class TestChatEndpoints:
    """Test suite for chat endpoints"""

    def test_create_conversation(self, client, sample_fund):
        """Test creating a new conversation"""
        response = client.post(
            "/api/chat/conversations",
            json={"fund_id": sample_fund.id}
        )

        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert data["fund_id"] == sample_fund.id

    def test_get_conversation(self, client, sample_conversation):
        """Test getting a conversation"""
        response = client.get(f"/api/chat/conversations/{sample_conversation.conversation_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == sample_conversation.conversation_id
        assert "messages" in data
        assert len(data["messages"]) == 2

    def test_get_conversation_not_found(self, client):
        """Test getting a non-existent conversation"""
        response = client.get("/api/chat/conversations/nonexistent-id")

        assert response.status_code == 404

    def test_delete_conversation(self, client, sample_conversation):
        """Test deleting a conversation"""
        response = client.delete(f"/api/chat/conversations/{sample_conversation.conversation_id}")

        assert response.status_code == 200

        # Verify conversation is deleted
        response = client.get(f"/api/chat/conversations/{sample_conversation.conversation_id}")
        assert response.status_code == 404


class TestDocumentsEndpoints:
    """Test suite for documents endpoints"""

    def test_list_documents(self, client, sample_document):
        """Test listing documents"""
        response = client.get("/api/documents")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_document(self, client, sample_document):
        """Test getting a specific document"""
        response = client.get(f"/api/documents/{sample_document.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_document.id
        assert data["file_name"] == sample_document.file_name

    def test_get_document_not_found(self, client):
        """Test getting a non-existent document"""
        response = client.get("/api/documents/9999")

        assert response.status_code == 404


class TestHealthEndpoint:
    """Test suite for health endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
