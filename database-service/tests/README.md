# Database Service Test Suite

This directory contains comprehensive tests for the Database Service, covering unit tests, integration tests, and end-to-end tests.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                # Shared fixtures and configuration
├── test_endpoints.py          # Unit tests for API endpoints
├── test_integration.py        # Integration tests for database operations
├── test_e2e.py               # End-to-end tests using launcher
├── test_runner.py            # Test runner and reporting utilities
├── pytest.ini               # Pytest configuration
├── requirements-test.txt     # Testing dependencies
└── README.md                # This file
```

## Test Categories

### 1. Unit Tests (`test_endpoints.py`)
- **API Endpoints**: All REST API endpoints functionality
- **Error Handling**: HTTP error responses and validation
- **Response Formats**: JSON response structure validation
- **Parameter Validation**: Query parameter validation
- **CORS Headers**: Cross-origin request handling

### 2. Integration Tests (`test_integration.py`)
- **Database Operations**: Complete database workflows
- **Data Retrieval**: Multi-table data retrieval workflows
- **Search Functionality**: Cross-entity search workflows
- **Statistics Calculation**: Database statistics workflows
- **Data Integrity**: Foreign key and consistency validation
- **Performance**: Query performance and pagination

### 3. End-to-End Tests (`test_e2e.py`)
- **Service Health**: Complete service health checks
- **Launcher Integration**: Tests using `--dev` flag
- **API Workflows**: Complete API interaction workflows
- **Error Handling**: End-to-end error scenarios
- **Performance**: Load testing and concurrent requests

## Running Tests

### Prerequisites

Install test dependencies:
```bash
cd /home/fml/dashboard_zero/database-service
pip install -r tests/requirements-test.txt
```

### Basic Test Execution

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_endpoints.py      # Unit tests
pytest tests/test_integration.py    # Integration tests
pytest tests/test_e2e.py           # End-to-end tests

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Using the Test Runner

The test runner provides automated execution and reporting:

```bash
# Run all tests
python tests/test_runner.py

# Run specific test types
python tests/test_runner.py --type unit
python tests/test_runner.py --type integration
python tests/test_runner.py --type e2e

# Run multiple test types
python tests/test_runner.py --types unit integration

# Run with verbose output
python tests/test_runner.py --verbose

# Run specific test
python tests/test_runner.py --test-name test_health_endpoint_healthy
```

### End-to-End Testing with Launcher

For complete end-to-end testing, use the launcher with `--dev` flag:

```bash
# Start services in development mode
./launch_dataviewer --dev

# In another terminal, run e2e tests
pytest tests/test_e2e.py -v
```

## Test Configuration

### Environment Variables

Set these environment variables for testing:

```bash
export DB_PATH="/path/to/test/database.db"
export API_HOST="localhost"
export API_PORT="5001"
export DEBUG="true"
```

### Database Setup

Tests use a temporary SQLite database with sample data. The database is created automatically with:

- **risks** table with sample risk data
- **controls** table with sample control data  
- **questions** table with sample question data
- **relationship tables** for entity mappings
- **file_metadata** table for version tracking

### Mock Configuration

Tests use mocked configuration to avoid external dependencies:

- Database path is mocked to use test database
- Configuration manager is mocked with test settings
- External services are mocked where appropriate

## Test Data

### Sample Data Structure

Tests use consistent sample data across all test categories:

```python
# Sample Risk
{
    "id": "AIR.001",
    "title": "Data Privacy Risk", 
    "description": "Risk of unauthorized access to sensitive data",
    "category": "Privacy"
}

# Sample Control
{
    "id": "AIGPC.1",
    "title": "Data Encryption",
    "description": "Implement encryption for data at rest and in transit",
    "domain": "Protect"
}

# Sample Question
{
    "id": "Q1",
    "text": "How is data privacy protected?",
    "category": "Privacy",
    "topic": "Data Protection"
}
```

### Relationship Data

Tests include relationship mappings:

- **Risk-Control**: AIR.001 ↔ AIGPC.1
- **Question-Risk**: Q1 ↔ AIR.001  
- **Question-Control**: Q1 ↔ AIGPC.1

## Test Coverage

### Target Coverage Goals

- **Unit Tests**: 95%+ coverage for API endpoints
- **Integration Tests**: 90%+ coverage for database operations
- **End-to-End Tests**: 80%+ coverage for complete workflows
- **Error Scenarios**: Comprehensive error handling tests

### Coverage Reporting

Generate coverage reports:

```bash
# HTML coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Terminal coverage report
pytest --cov=. --cov-report=term

# XML coverage report (for CI)
pytest --cov=. --cov-report=xml
```

## Continuous Integration

### GitHub Actions Integration

Tests are designed to run in CI environments:

```yaml
name: Database Service Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          cd database-service
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      - name: Run tests
        run: |
          cd database-service
          python tests/test_runner.py --type all
```

### Docker Integration

Tests can run in Docker containers:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY database-service/ .
RUN pip install -r requirements.txt
RUN pip install -r tests/requirements-test.txt
CMD ["python", "tests/test_runner.py", "--type", "all"]
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure test database is created properly
   - Check database path configuration
   - Verify SQLite3 is available

2. **Import Errors**
   - Ensure PYTHONPATH includes database-service directory
   - Check all dependencies are installed
   - Verify module structure

3. **Launcher Issues**
   - Ensure launcher script is executable
   - Check Docker is running for --dev mode
   - Verify port availability

4. **Timeout Issues**
   - Increase timeout values in pytest.ini
   - Check system resources
   - Verify network connectivity for e2e tests

### Debug Mode

Run tests in debug mode:

```bash
# Enable debug logging
export DEBUG="true"
pytest -v -s

# Use Python debugger
pytest --pdb

# Run specific test with debug
pytest tests/test_endpoints.py::TestHealthEndpoints::test_health_endpoint_healthy -v -s
```

## Contributing

### Adding New Tests

1. **Unit Tests**: Add to `test_endpoints.py`
2. **Integration Tests**: Add to `test_integration.py`  
3. **End-to-End Tests**: Add to `test_e2e.py`

### Test Naming Convention

- Test classes: `Test{FeatureName}`
- Test methods: `test_{specific_functionality}`
- Fixtures: `{purpose}_fixture`

### Test Documentation

- Document test purpose in docstrings
- Include expected behavior
- Note any special requirements
- Update this README for new test categories

## Performance Testing

### Load Testing

Run performance tests:

```bash
# Run performance tests only
pytest tests/test_integration.py::TestPerformanceWorkflows -v

# Run with performance markers
pytest -m performance -v
```

### Benchmarking

Compare performance across test runs:

```bash
# Run with duration reporting
pytest --durations=10

# Profile specific tests
pytest tests/test_integration.py::TestPerformanceWorkflows --profile
```

## Security Testing

### Input Validation

Tests verify proper input validation:

- SQL injection prevention
- Parameter validation
- Error message sanitization
- CORS configuration

### Authentication

Tests verify security measures:

- CORS headers
- Error handling
- Input sanitization
- Response validation
