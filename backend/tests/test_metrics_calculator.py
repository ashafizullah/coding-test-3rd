"""
Unit tests for MetricsCalculator service
"""
import pytest
from decimal import Decimal
from app.services.metrics_calculator import MetricsCalculator


class TestMetricsCalculator:
    """Test suite for MetricsCalculator"""

    def test_calculate_pic(self, db_session, complete_fund_with_transactions):
        """Test PIC calculation"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        pic = calculator.calculate_pic(fund.id)

        # PIC = Total Capital Calls - Adjustments
        # = (1,000,000 + 500,000 + 750,000) - 50,000
        # = 2,250,000 - 50,000 = 2,200,000
        assert pic == Decimal("2200000.00")

    def test_calculate_total_distributions(self, db_session, complete_fund_with_transactions):
        """Test total distributions calculation"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        total_dist = calculator.calculate_total_distributions(fund.id)

        # Total Distributions = 200,000 + 450,000 + 300,000 = 950,000
        assert total_dist == Decimal("950000.00")

    def test_calculate_dpi(self, db_session, complete_fund_with_transactions):
        """Test DPI calculation"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        dpi = calculator.calculate_dpi(fund.id)

        # DPI = Total Distributions / PIC
        # = 950,000 / 2,200,000 = 0.4318
        assert dpi == pytest.approx(0.4318, abs=0.0001)

    def test_calculate_nav(self, db_session, complete_fund_with_transactions):
        """Test NAV calculation"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        nav = calculator.calculate_nav(fund.id)

        # NAV = Total Capital Calls - Total Distributions - Adjustments
        # = 2,250,000 - 950,000 - 50,000 = 1,250,000
        assert nav == Decimal("1250000.00")

    def test_calculate_tvpi(self, db_session, complete_fund_with_transactions):
        """Test TVPI calculation"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        tvpi = calculator.calculate_tvpi(fund.id)

        # TVPI = (Total Distributions + NAV) / PIC
        # = (950,000 + 1,250,000) / 2,200,000
        # = 2,200,000 / 2,200,000 = 1.0
        assert tvpi == 1.0

    def test_calculate_rvpi(self, db_session, complete_fund_with_transactions):
        """Test RVPI calculation"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        rvpi = calculator.calculate_rvpi(fund.id)

        # RVPI = NAV / PIC
        # = 1,250,000 / 2,200,000 = 0.5682
        assert rvpi == pytest.approx(0.5682, abs=0.0001)

    def test_calculate_irr(self, db_session, complete_fund_with_transactions):
        """Test IRR calculation"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        irr = calculator.calculate_irr(fund.id)

        # IRR should be calculated based on cash flows
        # This is a basic test to ensure it returns a value
        assert irr is not None
        assert isinstance(irr, float)

    def test_calculate_all_metrics(self, db_session, complete_fund_with_transactions):
        """Test calculating all metrics at once"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        metrics = calculator.calculate_all_metrics(fund.id)

        # Verify all metrics are present
        assert "pic" in metrics
        assert "total_distributions" in metrics
        assert "dpi" in metrics
        assert "irr" in metrics
        assert "nav" in metrics
        assert "tvpi" in metrics
        assert "rvpi" in metrics

        # Verify values
        assert metrics["pic"] == 2200000.0
        assert metrics["total_distributions"] == 950000.0
        assert metrics["nav"] == 1250000.0
        assert metrics["dpi"] == pytest.approx(0.4318, abs=0.0001)
        assert metrics["tvpi"] == 1.0
        assert metrics["rvpi"] == pytest.approx(0.5682, abs=0.0001)

    def test_dpi_with_zero_pic(self, db_session, sample_fund):
        """Test DPI calculation when PIC is zero"""
        calculator = MetricsCalculator(db_session)

        dpi = calculator.calculate_dpi(sample_fund.id)

        # Should return 0 when PIC is zero
        assert dpi == 0.0

    def test_get_calculation_breakdown_dpi(self, db_session, complete_fund_with_transactions):
        """Test getting DPI calculation breakdown"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        breakdown = calculator.get_calculation_breakdown(fund.id, "dpi")

        assert breakdown["metric"] == "DPI"
        assert "formula" in breakdown
        assert "pic" in breakdown
        assert "total_distributions" in breakdown
        assert "result" in breakdown
        assert "transactions" in breakdown
        assert len(breakdown["transactions"]["capital_calls"]) == 3
        assert len(breakdown["transactions"]["distributions"]) == 3

    def test_get_calculation_breakdown_irr(self, db_session, complete_fund_with_transactions):
        """Test getting IRR calculation breakdown"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        breakdown = calculator.get_calculation_breakdown(fund.id, "irr")

        assert breakdown["metric"] == "IRR"
        assert "formula" in breakdown
        assert "cash_flows" in breakdown
        assert "result" in breakdown
        assert len(breakdown["cash_flows"]) == 6  # 3 capital calls + 3 distributions

    def test_get_calculation_breakdown_nav(self, db_session, complete_fund_with_transactions):
        """Test getting NAV calculation breakdown"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        breakdown = calculator.get_calculation_breakdown(fund.id, "nav")

        assert breakdown["metric"] == "NAV"
        assert "formula" in breakdown
        assert "total_calls" in breakdown
        assert "total_distributions" in breakdown
        assert "total_adjustments" in breakdown
        assert "result" in breakdown

    def test_get_calculation_breakdown_tvpi(self, db_session, complete_fund_with_transactions):
        """Test getting TVPI calculation breakdown"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        breakdown = calculator.get_calculation_breakdown(fund.id, "tvpi")

        assert breakdown["metric"] == "TVPI"
        assert "formula" in breakdown
        assert "total_distributions" in breakdown
        assert "nav" in breakdown
        assert "total_value" in breakdown
        assert "pic" in breakdown
        assert "result" in breakdown

    def test_get_calculation_breakdown_rvpi(self, db_session, complete_fund_with_transactions):
        """Test getting RVPI calculation breakdown"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        breakdown = calculator.get_calculation_breakdown(fund.id, "rvpi")

        assert breakdown["metric"] == "RVPI"
        assert "formula" in breakdown
        assert "nav" in breakdown
        assert "pic" in breakdown
        assert "result" in breakdown

    def test_get_calculation_breakdown_unknown_metric(self, db_session, sample_fund):
        """Test getting breakdown for unknown metric"""
        calculator = MetricsCalculator(db_session)

        breakdown = calculator.get_calculation_breakdown(sample_fund.id, "unknown")

        assert "error" in breakdown
        assert breakdown["error"] == "Unknown metric"

    def test_cash_flows_ordering(self, db_session, complete_fund_with_transactions):
        """Test that cash flows are properly ordered by date"""
        calculator = MetricsCalculator(db_session)
        fund = complete_fund_with_transactions["fund"]

        cash_flows = calculator._get_cash_flows(fund.id)

        # Verify cash flows are ordered by date
        for i in range(len(cash_flows) - 1):
            assert cash_flows[i]["date"] <= cash_flows[i + 1]["date"]

        # Verify capital calls are negative
        capital_call_flows = [cf for cf in cash_flows if cf["type"] == "capital_call"]
        for cf in capital_call_flows:
            assert cf["amount"] < 0

        # Verify distributions are positive
        distribution_flows = [cf for cf in cash_flows if cf["type"] == "distribution"]
        for cf in distribution_flows:
            assert cf["amount"] > 0
