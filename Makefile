.PHONY: test test-unit test-integration test-cov test-fast help install clean

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-fast        - Run fast tests (unit, not slow)"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make clean            - Clean test artifacts"
	@echo "  make run              - Run the application"
	@echo "  make migrate          - Run database migrations"

install:
	pip install -r requirements.txt

test:
	pytest

test-unit:
	pytest -m unit

test-integration:
	pytest -m integration

test-fast:
	pytest -m "unit and not slow"

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

run:
	python src/main.py

migrate:
	python -m alembic upgrade head

migrate-create:
	@read -p "Enter migration description: " desc; \
	python -m alembic revision --autogenerate -m "$$desc"
