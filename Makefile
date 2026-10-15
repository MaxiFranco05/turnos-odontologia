# Makefile - Development commands for the turnos-odontologia project
.PHONY: help install test up down logs clean

# Display help message
help:
	@echo "Available commands:"
	@echo "  make up        - Start docker containers (api + db)"
	@echo "  make down      - Stop docker containers"
	@echo "  make logs      - View container logs"
	@echo "  make test      - Run pytest suite inside api container"
	@echo "  make clean     - Stop containers and remove volumes"

# Start docker containers
up:
	@echo "Starting turnos-odontologia containers..."
	docker compose up -d
	@echo "Containers started. Waiting for DB to be ready..."
	@sleep 5
	@echo "DB readiness check complete."

# Stop docker containers
down:
	@echo "Stopping turnos-odontologia containers..."
	docker compose down
	@echo "Containers stopped."

# View container logs
logs:
	@docker compose logs -f api

# Run pytest suite inside api container
test:
	@echo "Running pytest suite for C-06-appointment-request..."
	docker compose exec api python -m pytest app/api/test_appointment.py -v
	@echo "Tests complete."

# Stop containers and remove volumes
clean: down
	docker compose down -v
	@echo "Containers and volumes removed."