.PHONY: help setup test lint format deploy-dev deploy-prod

help:
	@echo "Available commands:"
	@echo "  setup      - Initial project setup"
	@echo "  test       - Run all tests"
	@echo "  lint       - Run linting"
	@echo "  format     - Format code"
	@echo "  deploy-dev - Deploy to development"
	@echo "  deploy-prod- Deploy to production"

setup:
	@echo "Setting up development environment..."
	pip install -r data-pipelines/requirements.txt
	cd dbt-models && dbt deps

test:
	@echo "Running tests..."
	cd data-pipelines && python -m pytest tests/
	cd dbt-models && dbt test --target dev

lint:
	@echo "Running linting..."
	cd data-pipelines && flake8 src/
	cd data-pipelines && black --check src/

format:
	@echo "Formatting code..."
	cd data-pipelines && black src/
	cd dbt-models && dbt parse

deploy-dev:
	@echo "Deploying to development..."
	cd infrastructure/terraform/environments/dev && terraform apply -auto-approve
	cd dbt-models && dbt run --target dev

deploy-prod:
	@echo "Deploying to production..."
	cd infrastructure/terraform/environments/prod && terraform apply
	cd dbt-models && dbt run --target prod