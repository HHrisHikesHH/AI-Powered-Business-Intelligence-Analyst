SHELL := /bin/bash
.PHONY: help setup build up down restart logs clean migrate seed test

# Default target
help:
	@echo "AI-Powered Business Intelligence Analyst - Makefile Commands"
	@echo ""
	@echo "Setup & Build:"
	@echo "  make setup          - Initial setup (copy .env, build images)"
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run database migrations (creates schema)"
	@echo "  make seed           - Seed database with sample data"
	@echo "  make db-reset       - Reset database (drop and recreate)"
	@echo ""
	@echo "Development:"
	@echo "  make logs           - View logs from all services"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo "  make shell-db       - Open PostgreSQL shell"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove containers, volumes, and images"
	@echo "  make clean-volumes  - Remove only volumes (keeps images)"

# Setup: Copy .env.example to .env if it doesn't exist
setup:
	@if [ ! -f backend/.env ]; then \
		cp backend/.env.example backend/.env; \
		echo "Created backend/.env from .env.example"; \
		echo "Please edit backend/.env and add your GROQ_API_KEY"; \
	else \
		echo "backend/.env already exists"; \
	fi
	@echo "Setup complete. Run 'make build' to build Docker images."

# Build Docker images
build:
	docker-compose build

# Start all services
up:
	docker-compose up -d
	@echo "Services started. Use 'make logs' to view logs."

# Stop all services
down:
	docker-compose down

# Restart all services
restart: down up

# View logs
logs:
	docker-compose logs -f

# Database migration (schema creation)
migrate:
	@echo "Running database migrations..."
	@if [ ! -f .env ]; then \
		echo "Error: .env not found. Please create .env file with PostgreSQL credentials."; \
		exit 1; \
	fi
	@bash -c 'set -a; source .env; set +a; \
	PGPASSWORD=$${POSTGRES_PASSWORD} psql -h $${POSTGRES_HOST:-localhost} -p $${POSTGRES_PORT:-5432} -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-ai_bi_db} -f backend/database/init.sql'
	@echo "Migration complete."

# Seed database with sample data
seed:
	@echo "Seeding database with sample data..."
	@if [ ! -f .env ]; then \
		echo "Error: .env not found. Please create .env file with PostgreSQL credentials."; \
		exit 1; \
	fi
	@bash -c 'set -a; source .env; set +a; \
	PGPASSWORD=$${POSTGRES_PASSWORD} psql -h $${POSTGRES_HOST:-localhost} -p $${POSTGRES_PORT:-5432} -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-ai_bi_db} -f backend/database/seed_data.sql'
	@echo "Database seeded successfully."

# Reset database (drop and recreate)
db-reset:
	@echo "Resetting database..."
	@if [ ! -f .env ]; then \
		echo "Error: .env not found. Please create .env file with PostgreSQL credentials."; \
		exit 1; \
	fi
	@bash -c 'set -a; source .env; set +a; \
	echo "Dropping database $${POSTGRES_DB:-ai_bi_db}..."; \
	PGPASSWORD=$${POSTGRES_PASSWORD} psql -h $${POSTGRES_HOST:-localhost} -p $${POSTGRES_PORT:-5432} -U $${POSTGRES_USER:-postgres} -d postgres -c "DROP DATABASE IF EXISTS $${POSTGRES_DB:-ai_bi_db};"; \
	echo "Creating database $${POSTGRES_DB:-ai_bi_db}..."; \
	PGPASSWORD=$${POSTGRES_PASSWORD} psql -h $${POSTGRES_HOST:-localhost} -p $${POSTGRES_PORT:-5432} -U $${POSTGRES_USER:-postgres} -d postgres -c "CREATE DATABASE $${POSTGRES_DB:-ai_bi_db};"'
	@$(MAKE) migrate
	@$(MAKE) seed
	@echo "Database reset complete."

# Open shell in backend container
shell-backend:
	docker-compose exec backend /bin/bash

# Open PostgreSQL shell
shell-db:
	@if [ ! -f .env ]; then \
		echo "Error: .env not found. Please create .env file with PostgreSQL credentials."; \
		exit 1; \
	fi
	@bash -c 'set -a; source .env; set +a; \
	PGPASSWORD=$${POSTGRES_PASSWORD} psql -h $${POSTGRES_HOST:-localhost} -p $${POSTGRES_PORT:-5432} -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-ai_bi_db}'

# Run tests
test:
	docker-compose exec backend pytest -v

# Clean: Remove containers, volumes, and images
clean:
	docker-compose down -v --rmi all
	@echo "Cleaned up all containers, volumes, and images."

# Clean volumes only
clean-volumes:
	docker-compose down -v
	@echo "Removed volumes. Images are preserved."

