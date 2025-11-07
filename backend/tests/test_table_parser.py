"""
Unit tests for TableParser service
"""
import pytest
from datetime import date
from decimal import Decimal
from app.services.table_parser import TableParser


class TestTableParser:
    """Test suite for TableParser"""

    @pytest.fixture
    def parser(self):
        """Create a TableParser instance"""
        return TableParser()

    def test_parse_date_standard_format(self, parser):
        """Test parsing standard date format (YYYY-MM-DD)"""
        result = parser._parse_date("2023-01-15")
        assert result == date(2023, 1, 15)

    def test_parse_date_us_format(self, parser):
        """Test parsing US date format (MM/DD/YYYY)"""
        result = parser._parse_date("01/15/2023")
        assert result == date(2023, 1, 15)

    def test_parse_date_alternative_format(self, parser):
        """Test parsing alternative date format (DD-MM-YYYY)"""
        result = parser._parse_date("15-01-2023")
        assert result is not None
        # Note: This might parse as MM-DD-YYYY depending on implementation

    def test_parse_date_invalid(self, parser):
        """Test parsing invalid date"""
        result = parser._parse_date("invalid-date")
        assert result is None

    def test_parse_date_none(self, parser):
        """Test parsing None date"""
        result = parser._parse_date(None)
        assert result is None

    def test_parse_amount_simple(self, parser):
        """Test parsing simple amount"""
        result = parser._parse_amount("1000000")
        assert result == Decimal("1000000.00")

    def test_parse_amount_with_dollar_sign(self, parser):
        """Test parsing amount with dollar sign"""
        result = parser._parse_amount("$1,000,000.00")
        assert result == Decimal("1000000.00")

    def test_parse_amount_with_commas(self, parser):
        """Test parsing amount with commas"""
        result = parser._parse_amount("1,000,000.50")
        assert result == Decimal("1000000.50")

    def test_parse_amount_negative_parentheses(self, parser):
        """Test parsing negative amount with parentheses"""
        result = parser._parse_amount("($500,000)")
        assert result == Decimal("-500000.00")

    def test_parse_amount_negative_minus_sign(self, parser):
        """Test parsing negative amount with minus sign"""
        result = parser._parse_amount("-$500,000")
        assert result == Decimal("-500000.00")

    def test_parse_amount_decimal(self, parser):
        """Test parsing decimal amount"""
        result = parser._parse_amount("1234.56")
        assert result == Decimal("1234.56")

    def test_parse_amount_invalid(self, parser):
        """Test parsing invalid amount"""
        result = parser._parse_amount("not-a-number")
        assert result is None

    def test_parse_amount_none(self, parser):
        """Test parsing None amount"""
        result = parser._parse_amount(None)
        assert result is None

    def test_classify_table_type_capital_calls(self, parser):
        """Test classifying capital calls table"""
        table_info = {
            "headers": ["Date", "Call Type", "Amount", "Description"],
            "data": []
        }

        result = parser.classify_table_type(table_info)
        assert result == "capital_calls"

    def test_classify_table_type_distributions(self, parser):
        """Test classifying distributions table"""
        table_info = {
            "headers": ["Date", "Distribution Type", "Amount", "Recallable"],
            "data": []
        }

        result = parser.classify_table_type(table_info)
        assert result == "distributions"

    def test_classify_table_type_adjustments(self, parser):
        """Test classifying adjustments table"""
        table_info = {
            "headers": ["Date", "Adjustment Type", "Amount", "Category"],
            "data": []
        }

        result = parser.classify_table_type(table_info)
        assert result == "adjustments"

    def test_classify_table_type_unknown(self, parser):
        """Test classifying unknown table type"""
        table_info = {
            "headers": ["Random", "Headers", "Here"],
            "data": []
        }

        result = parser.classify_table_type(table_info)
        assert result is None

    def test_parse_capital_call_table(self, parser):
        """Test parsing capital call table"""
        table_info = {
            "headers": ["Date", "Call Type", "Amount", "Description"],
            "data": [
                ["2023-01-15", "Initial", "$1,000,000", "First call"],
                ["2023-06-20", "Follow-on", "$500,000", "Second call"],
            ]
        }

        result = parser.parse_capital_call_table(table_info)

        assert len(result) == 2
        assert result[0]["call_date"] == date(2023, 1, 15)
        assert result[0]["amount"] == Decimal("1000000.00")
        assert result[0]["call_type"] == "Initial"
        assert result[0]["description"] == "First call"

    def test_parse_distribution_table(self, parser):
        """Test parsing distribution table"""
        table_info = {
            "headers": ["Date", "Type", "Amount", "Recallable", "Description"],
            "data": [
                ["2023-03-15", "Dividend", "$200,000", "No", "First distribution"],
                ["2023-09-20", "Capital Return", "$450,000", "Yes", "Second distribution"],
            ]
        }

        result = parser.parse_distribution_table(table_info)

        assert len(result) == 2
        assert result[0]["distribution_date"] == date(2023, 3, 15)
        assert result[0]["amount"] == Decimal("200000.00")
        assert result[0]["distribution_type"] == "Dividend"
        assert result[0]["is_recallable"] is False

        assert result[1]["is_recallable"] is True

    def test_parse_adjustment_table(self, parser):
        """Test parsing adjustment table"""
        table_info = {
            "headers": ["Date", "Type", "Category", "Amount", "Description"],
            "data": [
                ["2023-02-10", "Expense", "Management Fee", "$50,000", "Annual fee"],
            ]
        }

        result = parser.parse_adjustment_table(table_info)

        assert len(result) == 1
        assert result[0]["adjustment_date"] == date(2023, 2, 10)
        assert result[0]["amount"] == Decimal("50000.00")
        assert result[0]["adjustment_type"] == "Expense"
        assert result[0]["category"] == "Management Fee"

    def test_parse_capital_call_table_with_invalid_rows(self, parser):
        """Test parsing capital call table with invalid rows"""
        table_info = {
            "headers": ["Date", "Call Type", "Amount", "Description"],
            "data": [
                ["2023-01-15", "Initial", "$1,000,000", "Valid call"],
                ["invalid-date", "Follow-on", "$500,000", "Invalid call"],
                ["2023-06-20", "Follow-on", "invalid-amount", "Invalid amount"],
            ]
        }

        result = parser.parse_capital_call_table(table_info)

        # Should only parse valid rows
        assert len(result) == 1
        assert result[0]["call_date"] == date(2023, 1, 15)

    def test_parse_distribution_table_recallable_variants(self, parser):
        """Test parsing recallable field with different values"""
        table_info = {
            "headers": ["Date", "Type", "Amount", "Recallable"],
            "data": [
                ["2023-01-15", "Dividend", "$100,000", "Yes"],
                ["2023-02-15", "Dividend", "$100,000", "True"],
                ["2023-03-15", "Dividend", "$100,000", "1"],
                ["2023-04-15", "Dividend", "$100,000", "No"],
                ["2023-05-15", "Dividend", "$100,000", "False"],
                ["2023-06-15", "Dividend", "$100,000", "0"],
            ]
        }

        result = parser.parse_distribution_table(table_info)

        assert len(result) == 6
        # First three should be recallable
        assert result[0]["is_recallable"] is True
        assert result[1]["is_recallable"] is True
        assert result[2]["is_recallable"] is True
        # Last three should not be recallable
        assert result[3]["is_recallable"] is False
        assert result[4]["is_recallable"] is False
        assert result[5]["is_recallable"] is False

    def test_parse_empty_table(self, parser):
        """Test parsing empty table"""
        table_info = {
            "headers": ["Date", "Amount"],
            "data": []
        }

        result = parser.parse_capital_call_table(table_info)
        assert result == []

    def test_standardize_header_names(self, parser):
        """Test that parser can handle various header name variants"""
        # Test with different header naming conventions
        table_info = {
            "headers": ["date", "CALL TYPE", "Amount ($)", "notes"],
            "data": [
                ["2023-01-15", "Initial", "1000000", "Test"],
            ]
        }

        result = parser.parse_capital_call_table(table_info)

        # Should successfully parse despite header variations
        assert len(result) == 1
        assert result[0]["amount"] == Decimal("1000000.00")
