# Test Suite

Comprehensive test suite for the Secret House Booking Bot.

## Overview

The test suite covers:
- **Unit Tests**: Helpers, services, models, and enums
- **Integration Tests**: Redis services and external integrations
- **Test Coverage**: Automated coverage reporting

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html to view coverage report
```

## Test Organization

```
tests/
├── conftest.py                          # Shared fixtures and configuration
├── test_string_helper.py                # String helper unit tests
├── test_date_time_helper.py             # Date/time helper unit tests
├── test_calculation_rate_service.py     # Rate calculation unit tests
├── test_date_pricing_service.py         # Date pricing tests
├── test_models_enums.py                 # Model and enum tests
├── test_redis_integration.py            # Redis integration tests
├── test_calculation_rate_integration.py # Rate calculation integration tests
└── README.md                            # This file
```

## Test Markers

Use pytest markers to run specific test categories:

### Unit Tests (Fast)
```bash
pytest -m unit
```
Tests that don't require external dependencies (databases, APIs, etc.)

### Integration Tests
```bash
pytest -m integration
```
Tests that require external services like Redis, PostgreSQL, or external APIs.

### Slow Tests
```bash
pytest -m slow
```
Tests that take longer to run (can be excluded during development).

### Service-Specific Tests
```bash
# Tests requiring database
pytest -m requires_db

# Tests requiring Redis
pytest -m requires_redis

# Tests requiring external APIs
pytest -m requires_external
```

### Exclude Markers
```bash
# Run fast tests only (exclude slow and integration)
pytest -m "unit and not slow"

# Run all except external dependencies
pytest -m "not requires_external"
```

## Writing Tests

### Basic Unit Test

```python
import pytest

@pytest.mark.unit
class TestMyFunction:
    def test_basic_case(self):
        result = my_function(input_data)
        assert result == expected_output
```

### Using Fixtures

```python
@pytest.mark.unit
class TestWithFixtures:
    def test_with_sample_data(self, sample_rental_price):
        # sample_rental_price is provided by conftest.py
        assert sample_rental_price.price == 700
```

### Integration Test

```python
@pytest.mark.integration
@pytest.mark.requires_redis
class TestRedisIntegration:
    def test_redis_connection(self, mock_redis_client):
        # Test with mocked or real Redis
        pass
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

## Available Fixtures

Defined in [conftest.py](conftest.py):

### Date/Time Fixtures
- `test_date` - Standard test date (2024-06-15)
- `test_datetime` - Standard test datetime

### Model Fixtures
- `sample_rental_price` - Sample RentalPrice instance
- `sample_date_pricing_rules` - Sample pricing rules list
- `sample_booking_data` - Sample booking dictionary
- `sample_gift_certificate_data` - Sample gift certificate dictionary

### Mock Fixtures
- `mock_telegram_update` - Mock Telegram Update object
- `mock_telegram_context` - Mock Telegram Context object
- `mock_file_service` - Mocked FileService
- `mock_redis_service` - Mocked Redis service
- `mock_database_service` - Mocked DatabaseService
- `mock_calendar_service` - Mocked CalendarService
- `mock_gpt_service` - Mocked GPTService
- `mock_settings_service` - Mocked SettingsService

### Utility Fixtures
- `temp_test_db` - Temporary test database path

## Running Tests in CI/CD

### GitHub Actions Example
```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=src --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Best Practices

1. **Keep tests isolated**: Each test should be independent
2. **Use descriptive names**: Test names should describe what they test
3. **Mock external dependencies**: Don't call real APIs in unit tests
4. **Test edge cases**: Include tests for boundary conditions
5. **Keep tests fast**: Unit tests should run in milliseconds
6. **Use fixtures**: Reuse common test data via fixtures
7. **Mark appropriately**: Use markers to categorize tests

## Coverage Goals

- **Target**: 80%+ code coverage
- **Critical paths**: 100% coverage for booking workflow
- **Helpers**: 90%+ coverage
- **Services**: 80%+ coverage

## Troubleshooting

### Tests fail with import errors
```bash
# Make sure you're in the project root
cd /path/to/secret-house-booking-bot
pytest
```

### Redis connection errors
```bash
# Make sure Redis is running (for integration tests)
docker run -d -p 6379:6379 redis

# Or skip Redis tests
pytest -m "not requires_redis"
```

### Slow test execution
```bash
# Run only fast unit tests
pytest -m "unit and not slow"

# Use pytest-xdist for parallel execution
pip install pytest-xdist
pytest -n auto
```

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass: `pytest`
3. Check coverage: `pytest --cov=src`
4. Add appropriate markers
5. Update this README if adding new test categories

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [freezegun](https://github.com/spulec/freezegun) - Time mocking
