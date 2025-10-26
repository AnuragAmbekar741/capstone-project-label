# Simple FastAPI Makefile

.PHONY: help run dev install

# Default target
help:
	@echo "Available commands:"
	@echo "  run    - Run the FastAPI app"
	@echo "  dev    - Run in development mode with reload"
	@echo "  install - Install dependencies"

# Run the application
run:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run in development mode with auto-reload
dev:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Install dependencies
install:
	poetry install

# Initialize Aerich migrations (run once)
migrate-init:
	poetry run aerich init -t app.config.TORTOISE_ORM

# Generate migration for model changes
migrate-gen:
	poetry run aerich migrate


# Apply migrations to database
migrate-up:
	poetry run aerich upgrade

git-profile:
	git config --global user.name "AnuragAmbekar741"
	git config --global user.email "anuragambekar1997@gmail.com"