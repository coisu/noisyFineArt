DOCKER_COMPOSE = docker-compose
PYTHON = python
DB_INIT_SCRIPT = db_init.py
SERVICE_NAME = noisy-art

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

build:
	@echo "Building Docker image..."
	$(DOCKER_COMPOSE) build

up:
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
	@curl "http://localhost:5000/search?keyword=강렬한" || echo "Error: Search failed."

clean:
	@echo "Cleaning up..."
	rm -rf history
	rm -rf db/history.db
	$(DOCKER_COMPOSE) down --volumes --remove-orphans

reset-db:
	@echo "Resetting the database..."
	rm -rf db/history.db
	make init-db

.PHONY: help init-db build up down logs test clean reset-db
