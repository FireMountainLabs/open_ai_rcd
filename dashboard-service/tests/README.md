# Dashboard Service Test Suite

This directory contains comprehensive tests for the dashboard service, including unit tests, integration tests, and end-to-end tests.

## Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest configuration and shared fixtures
├── pytest.ini                 # Pytest settings
├── requirements-test.txt       # Test dependencies
├── test_runner.py             # Test execution script
├── README.md                  # This file
├── test_config_manager.py     # Unit tests for ConfigManager
├── test_database_api_client.py # Unit tests for DatabaseAPIClient
├── test_api_endpoints.py      # API endpoint tests
├── test_integration.py        # Integration tests using launcher
└── test_e2e.py               # End-to-end tests
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- **ConfigManager tests**: Configuration loading, validation, and environment variable handling
- **DatabaseAPIClient tests**: API client functionality and error handling
- **API endpoint tests**: Individual endpoint functionality and response formats

### Integration Tests (`@pytest.mark.integration`)
- **Service integration**: Tests using the launcher with `--dev` flag
- **Database connectivity**: Tests that verify database service communication
- **Performance tests**: Response time and concurrent request handling
- **CORS functionality**: Cross-origin request handling

### End-to-End Tests (`@pytest.mark.e2e`)
- **Complete workflows**: Full user journeys from start to finish
- **Data consistency**: Verification that data is consistent across endpoints
- **Search functionality**: Comprehensive search testing
- **Error handling**: Edge cases and error scenarios

## Account Cleanup

Tests that create real user accounts (integration/e2e tests) automatically clean up accounts after test execution. The `account_cleanup` fixture tracks accounts created during tests and deletes them in teardown.

### Automatic Cleanup

The `cleanup_test_accounts` fixture (autouse) automatically tracks accounts created via:
- `/register` endpoint
- `/api/auth/register` endpoint  
- `/api/admin/create-user` endpoint

### Manual Cleanup

For tests that create accounts in other ways, use the `account_cleanup` fixture directly:

```python
def test_create_user(account_cleanup):
    # Create account
    response = client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    
    # Track for cleanup
    username = response.json()["user"]["username"]
    account_cleanup.add(username)
    
    # Test continues...
```

The account will be automatically deleted after the test completes.

### Environment Variables

For cleanup to work properly, set these environment variables:
- `AUTH_SERVICE_URL`: URL of the authentication service
- `DASHBOARD_URL`: URL of the dashboard service
- `ADMIN_USERNAME`: Admin username for cleanup operations (default: "admin")
- `ADMIN_PASSWORD`: Admin password for cleanup operations (default: "admin")

## Prerequisites

### Required Dependencies
Install test dependencies:
```bash
pip install -r requirements-test.txt
```

### Required Services
For integration and e2e tests, the following services must be available:
- Database service (port 5001)
- Authentication service (port 5003) - optional for some tests
- Launcher script (`launch_dataviewer`)

## Running Tests

### Using the Test Runner Script

The `test_runner.py` script provides convenient ways to run different test categories:

```bash
# Run all tests
python test_runner.py all

# Run only unit tests (fast, no external dependencies)
python test_runner.py unit

# Run only integration tests (requires launcher)
python test_runner.py integration

# Run only end-to-end tests (requires launcher)
python test_runner.py e2e

# Run launcher-based tests (integration + e2e)
python test_runner.py launcher

# Run quick tests (unit tests only, with coverage)
python test_runner.py quick
```

### Using Pytest Directly

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e

# Run with coverage
pytest --cov=../ --cov-report=html

# Run in parallel
pytest -n auto

# Run specific test file
pytest test_api_endpoints.py

# Run with verbose output
pytest -v -s
```

### Using the Launcher for Integration Tests

For integration and e2e tests, use the launcher with the `--dev` flag:

```bash
# Start the system
docker compose up --no-auth

# In another terminal, run tests
pytest -m integration
pytest -m e2e
```


### Pytest Markers
Tests are organized using pytest markers:
- `unit`: Unit tests for individual components
- `integration`: Integration tests using launcher
- `e2e`: End-to-end tests
- `api`: API endpoint tests
- `auth`: Authentication tests
- `config`: Configuration tests
- `database`: Tests requiring database service
- `slow`: Slow running tests
- `launcher`: Tests requiring launcher

## Test Fixtures

### Common Fixtures
- `temp_dir`: Temporary directory for test data
- `test_config`: Test configuration file
- `mock_config_manager`: Mock configuration manager
- `flask_app`: Flask application instance
- `client`: Test client for HTTP requests
- `mock_database_api_client`: Mock database API client
- `mock_auth_service`: Mock authentication service

### Data Fixtures
- `sample_risk_data`: Sample risk data
- `sample_control_data`: Sample control data
- `sample_user_data`: Sample user data
- `test_data_generator`: Utility for generating test data

## Coverage Reports

Coverage reports are generated in HTML format and can be viewed by opening `htmlcov/index.html` in a web browser.

```bash
# Generate coverage report
pytest --cov=../ --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Debugging Tests

### Running Individual Tests
```bash
# Run specific test
pytest test_api_endpoints.py::TestHealthEndpoints::test_health_endpoint_success

# Run with debugging
pytest -v -s --pdb test_api_endpoints.py
```

### Verbose Output
```bash
# Show all print statements and logs
pytest -v -s

# Show test names as they run
pytest -v
```

### Test Discovery
```bash
# List all tests without running them
pytest --collect-only

# List tests matching a pattern
pytest --collect-only -k "health"
```

## Continuous Integration

### GitHub Actions
The test suite is designed to work with GitHub Actions. See the main repository's `.github/workflows/` directory for CI configuration.

### Local CI Testing
For local CI testing and debugging:

```bash
# Run all tests with coverage
python test_runner.py all --coverage

# Run specific test category
python test_runner.py unit --coverage --verbose

# Run with parallel execution
python test_runner.py unit --parallel
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the dashboard-service directory
2. **Port Conflicts**: Make sure ports 5001, 5002, and 5003 are available
3. **Launcher Issues**: Ensure the launcher script is executable and in the correct location
4. **Database Connection**: Verify the database service is running and accessible

### Debug Mode
```bash
# Run with debug output
PYTHONPATH=. pytest -v -s --tb=long

# Run specific failing test with debug
pytest -v -s --pdb test_api_endpoints.py::TestHealthEndpoints::test_health_endpoint_success
```

### Test Isolation
Each test is isolated and should not depend on other tests. If tests are failing due to shared state, check:
- Database cleanup in fixtures
- Mock object state
- Environment variable isolation
- File system cleanup

## Contributing

When adding new tests:

1. Follow the existing naming conventions
2. Use appropriate pytest markers
3. Add fixtures to `conftest.py` if they'll be reused
4. Include both positive and negative test cases
5. Add docstrings explaining what each test verifies
6. Update this README if adding new test categories or patterns

## Performance Considerations

- Unit tests should run quickly (< 1 second each)
- Integration tests may take longer due to service startup
- E2E tests are the slowest and should be run selectively
- Use `@pytest.mark.slow` for tests that take > 5 seconds
- Consider using `pytest-xdist` for parallel execution of unit tests
