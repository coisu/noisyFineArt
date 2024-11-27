DOCKER_COMPOSE = docker-compose
PYTHON = python3
DB_INIT_SCRIPT = db_init.py
SERVICE_NAME = noisy-art
DB_FILE = db/history.db

all: build up

help:
	@echo "Usage:"
	@echo "  make init-db         - Initialize the SQLite database"
	@echo "  make build           - Build the Docker image"
	@echo "  make up              - Start the Docker container"
	@echo "  make down            - Stop and remove the Docker container"
	@echo "  make logs            - Show logs from the Docker container"
	@echo "  make test            - Test the API endpoints"
	@echo "  make clean           - Clean up generated files and containers"
	@echo "  make reset-db        - Reset the database (delete and reinitialize)"

init-db:
	@echo "Initializing the database..."
	$(PYTHON) $(DB_INIT_SCRIPT)

build: decrypt-mama
	@echo "Building Docker image..."
	$(DOCKER_COMPOSE) build

check-db:
	@echo "Checking if database exists..."
	@if [ ! -f $(DB_FILE) ]; then \
		echo "Database not found. Initializing..."; \
		$(MAKE) init-db; \
	else \
		echo "Database already exists. Skipping initialization."; \
	fi

up: check-db
	@echo "Starting Docker container..."
	$(DOCKER_COMPOSE) up -d

down:
	@echo "Stopping Docker container..."
	$(DOCKER_COMPOSE) down

logs:
	@echo "Showing logs from Docker container..."
	$(DOCKER_COMPOSE) logs -f $(SERVICE_NAME)

# API test
test:
	@echo "Testing API endpoints..."
	@curl -X POST -F "file=@example.wav" http://localhost:5000/upload || echo "Error: Upload failed."
	@curl "http://localhost:5000/search?keyword=energetic" || echo "Error: Search failed."

fclean:
	@echo "Force cleaning up..."
	sudo rm -rf history
	sudo rm -rf $(DB_FILE)
	$(DOCKER_COMPOSE) down --volumes --remove-orphans || true

reset-db:
	@echo "Resetting the database..."
	rm -rf $(DB_FILE)
	$(MAKE) init-db

decrypt-mama:
	gpg -d -o .env .env.gpg

.PHONY: help init-db build up down logs test clean reset-db decrypt-mama check-db
