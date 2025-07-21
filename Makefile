.PHONY: help install dev test lint format clean build run

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_PROD = docker-compose -f docker-compose.yml -f docker-compose.prod.yml
APP_NAME = evergreen-pipeline
VERSION ?= latest

# Default target
help:
	@echo "AI Content Generation Pipeline - Management Commands"
	@echo ""
	@echo "Local Development:"
	@echo "  make install        Install Python dependencies"
	@echo "  make dev           Run development server (local)"
	@echo "  make test          Run test suite"
	@echo "  make lint          Run code linting"
	@echo "  make format        Format code"
	@echo "  make clean         Clean generated files"
	@echo ""
	@echo "Docker Development:"
	@echo "  make build         Build Docker images"
	@echo "  make up            Start all services (Docker)"
	@echo "  make down          Stop all services"
	@echo "  make logs          View logs from all services"
	@echo "  make shell         Open shell in API container"
	@echo "  make ps            Show running containers"
	@echo ""
	@echo "Database Commands:"
	@echo "  make migrate       Run database migrations"
	@echo "  make db-shell      Open PostgreSQL shell"
	@echo "  make db-backup     Backup database"
	@echo "  make db-restore    Restore database from backup"
	@echo ""
	@echo "Production Commands:"
	@echo "  make prod-up       Start production services"
	@echo "  make prod-down     Stop production services"
	@echo "  make prod-deploy   Build and deploy to production"
	@echo ""
	@echo "Monitoring:"
	@echo "  make monitor       Open Flower monitoring UI"
	@echo "  make stats         Show container statistics"
	@echo "  make health        Check service health"

# Local development commands
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	uvicorn api.main:app --reload --port 8000

test:
	pytest tests/ -v --cov=src --cov-report=html

test-docker:
	$(DOCKER_COMPOSE) run --rm api pytest tests/ -v

lint:
	flake8 src/ api/ workers/
	mypy src/ api/ workers/
	pylint src/ api/ workers/

format:
	black src/ api/ workers/ tests/
	isort src/ api/ workers/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/
	rm -rf output/temp/*

# Docker commands
build:
	$(DOCKER_COMPOSE) build --no-cache

build-fast:
	$(DOCKER_COMPOSE) build

up:
	$(DOCKER_COMPOSE) up -d
	@echo "Services started. API: http://localhost:8000, Flower: http://localhost:5555"

run: up

down:
	$(DOCKER_COMPOSE) down

stop: down

restart:
	$(DOCKER_COMPOSE) restart

logs:
	$(DOCKER_COMPOSE) logs -f --tail=100

logs-api:
	$(DOCKER_COMPOSE) logs -f api --tail=100

logs-worker:
	$(DOCKER_COMPOSE) logs -f worker --tail=100

shell:
	$(DOCKER_COMPOSE) exec api /bin/bash

shell-worker:
	$(DOCKER_COMPOSE) exec worker /bin/bash

ps:
	$(DOCKER_COMPOSE) ps

# Database commands
migrate:
	$(DOCKER_COMPOSE) run --rm api alembic upgrade head

migrate-create:
	$(DOCKER_COMPOSE) run --rm api alembic revision --autogenerate -m "$(MESSAGE)"

db-shell:
	$(DOCKER_COMPOSE) exec db psql -U pipeline -d pipeline

db-backup:
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec -T db pg_dump -U pipeline pipeline | gzip > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql.gz
	@echo "Database backed up to backups/backup_$(shell date +%Y%m%d_%H%M%S).sql.gz"

db-restore:
	@test -n "$(FILE)" || (echo "Please specify FILE=backup_file.sql.gz" && exit 1)
	@gunzip -c $(FILE) | $(DOCKER_COMPOSE) exec -T db psql -U pipeline pipeline
	@echo "Database restored from $(FILE)"

# Production commands
prod-build:
	docker build -t $(APP_NAME):$(VERSION) .
	docker tag $(APP_NAME):$(VERSION) $(APP_NAME):latest

prod-up:
	$(DOCKER_COMPOSE_PROD) up -d

prod-down:
	$(DOCKER_COMPOSE_PROD) down

prod-deploy: prod-build
	@echo "Deploying version $(VERSION) to production..."
	$(DOCKER_COMPOSE_PROD) pull
	$(DOCKER_COMPOSE_PROD) up -d
	@echo "Deployment complete!"

# Monitoring commands
monitor:
	@echo "Opening Flower monitoring UI..."
	@open http://localhost:5555 || xdg-open http://localhost:5555 || echo "Visit http://localhost:5555"

stats:
	docker stats --no-stream

health:
	@echo "Checking service health..."
	@$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "API Health:"
	@curl -sf http://localhost:8000/health || echo "API is not healthy"
	@echo ""
	@echo "Database Health:"
	@$(DOCKER_COMPOSE) exec -T db pg_isready -U pipeline || echo "Database is not healthy"
	@echo ""
	@echo "Redis Health:"
	@$(DOCKER_COMPOSE) exec -T redis redis-cli ping || echo "Redis is not healthy"

# Development tools
dev-tools:
	$(DOCKER_COMPOSE) --profile dev-tools up -d
	@echo "Dev tools started. Adminer: http://localhost:8080, MailHog: http://localhost:8025"

# Cleanup commands
reset: down
	$(DOCKER_COMPOSE) down -v
	rm -rf output/*

clean-docker:
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f

clean-all: clean clean-docker
	docker system prune -af --volumes

# Initialize project
init: build migrate
	@echo "Project initialized successfully!"
	@echo "Run 'make up' to start the services"

# Quick commands
quick-start: init up
	@echo "Application is running at http://localhost:8000"

rebuild: down build up
	@echo "Services rebuilt and restarted"
