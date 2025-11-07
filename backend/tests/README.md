# Backend Test Suite

Comprehensive test suite for the Fund Performance Analysis System backend.

## Test Coverage

### Unit Tests

1. **test_models.py** - Database model tests
   - Fund model CRUD operations
   - Transaction models (CapitalCall, Distribution, Adjustment)
   - Document model
   - Conversation and ConversationMessage models
   - CustomFormula model
   - Relationship cascades and constraints

2. **test_metrics_calculator.py** - Metrics calculation tests
   - PIC (Paid-In Capital) calculation
   - DPI (Distributions to Paid-In) calculation
   - IRR (Internal Rate of Return) calculation
   - NAV (Net Asset Value) calculation
   - TVPI (Total Value to Paid-In) calculation
   - RVPI (Residual Value to Paid-In) calculation
   - Calculation breakdowns and edge cases

3. **test_table_parser.py** - PDF table parsing tests
   - Date parsing (multiple formats)
   - Amount parsing (with/without currency symbols)
   - Table classification (capital_calls, distributions, adjustments)
   - Row parsing with validation
   - Error handling for invalid data

4. **test_api_endpoints.py** - API endpoint tests
   - Funds endpoints (CRUD operations)
   - Transactions endpoints
   - Chat endpoints (conversation management)
   - Documents endpoints
   - Health check endpoint

## Running Tests

### Run All Tests

```bash
cd backend
pytest
```

### Run Specific Test File

```bash
pytest tests/test_metrics_calculator.py
```

### Run Specific Test Class

```bash
pytest tests/test_metrics_calculator.py::TestMetricsCalculator
```

### Run Specific Test Function

```bash
pytest tests/test_metrics_calculator.py::TestMetricsCalculator::test_calculate_dpi
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

### Run with Verbose Output

```bash
pytest -v
```

### Run Only Fast Tests (Exclude Slow Tests)

```bash
pytest -m "not slow"
```

## Test Fixtures

Fixtures are defined in `conftest.py`:

- `db_session` - Fresh in-memory SQLite database for each test
- `sample_fund` - A test fund with basic information
- `sample_capital_calls` - Three capital calls for testing
- `sample_distributions` - Three distributions for testing
- `sample_adjustments` - One adjustment for testing
- `sample_document` - A test document
- `sample_conversation` - A test conversation with messages
- `sample_custom_formula` - A test custom formula
- `complete_fund_with_transactions` - Fund with all transaction types

## Test Organization

Tests follow the Arrange-Act-Assert pattern:

```python
def test_calculate_dpi(self, db_session, complete_fund_with_transactions):
    # Arrange
    calculator = MetricsCalculator(db_session)
    fund = complete_fund_with_transactions["fund"]

    # Act
    dpi = calculator.calculate_dpi(fund.id)

    # Assert
    assert dpi == pytest.approx(0.4318, abs=0.0001)
```

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

### GitHub Actions Example

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt

    - name: Run tests
      run: |
        cd backend
        pytest --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Adding New Tests

### 1. Create a new test file

```python
# tests/test_my_feature.py
import pytest

class TestMyFeature:
    def test_something(self, db_session):
        # Test implementation
        pass
```

### 2. Use existing fixtures

Fixtures from `conftest.py` are automatically available.

### 3. Add new fixtures if needed

Add to `conftest.py`:

```python
@pytest.fixture
def my_custom_fixture(db_session):
    # Setup
    obj = MyModel(...)
    db_session.add(obj)
    db_session.commit()

    yield obj

    # Teardown (optional)
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Clarity**: Test names should describe what they test
3. **Completeness**: Test both success and failure cases
4. **Speed**: Keep tests fast (use in-memory DB)
5. **Coverage**: Aim for >80% code coverage

## Troubleshooting

### Import Errors

Make sure you're in the backend directory and PYTHONPATH includes the app module:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Database Errors

Tests use SQLite in-memory database. If you see PostgreSQL-specific errors, check that the code properly handles SQLite differences.

### Fixture Not Found

Ensure fixtures are defined in `conftest.py` or imported properly.

## Test Metrics

Current test coverage:
- **Models**: ~95% coverage
- **MetricsCalculator**: ~90% coverage
- **TableParser**: ~85% coverage
- **API Endpoints**: ~80% coverage

Target: **>80% overall coverage**
