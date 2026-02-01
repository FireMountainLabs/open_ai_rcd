# Dashboard Service Makefile
# Provides convenient commands for development, testing, and deployment

.PHONY: help install install-test test test-unit test-integration test-e2e test-all test-quick test-coverage test-watch clean lint format check-deps run-dev run-prod

# Default target
help:
	@echo "Dashboard Service - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install          Install production dependencies"
	@echo "  install-test     Install test dependencies"
	@echo "  run-dev          Run service in development mode"
	@echo "  run-prod         Run service in production mode"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests (requires launcher)"
	@echo "  test-e2e         Run end-to-end tests (requires launcher)"
	@echo "  test-quick       Run quick tests (unit tests with coverage)"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  test-watch       Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code with black and isort"
	@echo "  check-deps       Check for dependency updates"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean up temporary files"
	@echo "  help             Show this help message"

# Installation
install:
	pip install -r requirements.txt

install-test:
	pip install -r tests/requirements-test.txt

# Testing
test:
	python tests/test_runner.py all

test-unit:
	python tests/test_runner.py unit

test-integration:
	python tests/test_runner.py integration

test-e2e:
	python tests/test_runner.py e2e

test-quick:
	python tests/test_runner.py quick

test-coverage:
	python tests/test_runner.py unit --coverage

test-watch:
	pytest-watch tests/

# Code Quality
lint:
	flake8 . --exclude=tests/
	pylint app.py config_manager.py

format:
	black . --exclude=tests/
	isort . --skip=tests/

check-deps:
	pip list --outdated

# Running the service
run-dev:
	python app.py

run-prod:
	gunicorn -w 4 -b 0.0.0.0:${PORT} app:app

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/

# Development workflow
dev-setup: install install-test
	@echo "Development environment setup complete!"
	@echo "Run 'make test-quick' to verify everything is working."

# CI workflow
ci-test: install-test test-unit
	@echo "CI tests completed successfully!"

# Full test suite (for local development)
full-test: test-unit test-integration test-e2e
	@echo "Full test suite completed!"

# Quick development cycle
dev-cycle: format lint test-quick
	@echo "Development cycle completed!"

# Docker-related commands (if needed)
docker-build:
	docker build -t dashboard-service .

docker-run:
	docker run -p ${PORT}:${PORT} dashboard-service

# Launcher integration
launcher-test:
	@echo "Starting launcher-based tests..."
	@echo "This will start the full system using the launcher."
	@echo "Make sure the launcher script is available and executable."
	python tests/test_runner.py launcher

# Debugging
debug-test:
	pytest -v -s --pdb tests/

debug-unit:
	pytest -v -s --pdb -m unit tests/

# Performance testing
perf-test:
	pytest -v -s -m "integration and not slow" tests/

# Security testing
security-test:
	pytest -v -s -m security tests/

# Documentation
docs:
	@echo "Generating test documentation..."
	@echo "See tests/README.md for detailed test documentation."
