.PHONY: help install install-dev test test-cov lint format clean docker-build docker-run docker-stop

help: ## Show this help message
	@echo "LLM Gateway - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

lint: ## Run linting
	flake8 app/ tests/
	isort --check-only app/ tests/
	black --check app/ tests/

format: ## Format code
	isort app/ tests/
	black app/ tests/

clean: ## Clean up cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf .coverage htmlcov/
	rm -rf dist/ build/ *.egg-info/

docker-build: ## Build Docker image
	docker build -f deployments/Dockerfile -t llm-gateway .

docker-run: ## Run with Docker Compose (development)
	docker-compose -f deployments/docker-compose.yml up -d

docker-run-prod: ## Run with Docker Compose (production)
	docker-compose -f deployments/docker-compose.prod.yml up -d

docker-stop: ## Stop Docker containers
	docker-compose -f deployments/docker-compose.yml down
	docker-compose -f deployments/docker-compose.prod.yml down

docker-logs: ## Show Docker logs
	docker-compose -f deployments/docker-compose.prod.yml logs -f

start: ## Start production services
	chmod +x deployments/start.sh
	./deployments/start.sh

stop: ## Stop production services
	chmod +x deployments/stop.sh
	./deployments/stop.sh

health: ## Check service health
	curl -f http://localhost:8000/health || echo "Service not responding"

config: ## Show configuration
	python config_cli.py show --summary

validate: ## Validate configuration
	python config_cli.py validate

setup: install-dev ## Setup development environment
	cp env.example .env
	@echo "Development environment setup complete!"
	@echo "Please edit .env file with your configuration"

dev: ## Start development server
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

check: lint test ## Run all checks (lint + test)

pre-commit: format lint test ## Run pre-commit checks

check-docs: ## Check documentation consistency
	python scripts/check_documentation.py

clean: ## Clean up cache and temporary files
	python scripts/clean_project.py --dry-run

clean-force: ## Force clean up cache and temporary files
	python scripts/clean_project.py

docs-check: check-docs ## Alias for check-docs 