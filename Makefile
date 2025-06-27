# DOOM-COBOL Makefile
# Orchestrates the entire system

.PHONY: all build up down logs clean test doom-start doom-stop help

# Default target
all: help

# Build all Docker images
build:
	@echo "Building Docker images..."
	docker-compose build --parallel

# Start the entire system
up: build
	@echo "Starting DOOM-COBOL system..."
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "System ready!"
	@echo "  - COBOL Interface: telnet localhost 9999"
	@echo "  - Web UI: http://localhost:8080"
	@echo "  - TN3270 Terminal: tn3270://localhost:3270"
	@echo "  - FTP: ftp://localhost:2122"

# Stop the system
down:
	@echo "Stopping DOOM-COBOL system..."
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# View specific service logs
logs-%:
	docker-compose logs -f $*

# Clean up everything
clean: down
	@echo "Cleaning up..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# Run tests
test:
	@echo "Testing COBOL interface..."
	@echo "MOVE FORWARD" | nc localhost 9999
	@sleep 1
	@echo "TURN RIGHT 90" | nc localhost 9999
	@sleep 1
	@echo "SHOOT" | nc localhost 9999
	@sleep 1
	@echo "STATUS" | nc localhost 9999

# Start DOOM (example for Linux)
doom-start:
	@echo "Starting DOOM..."
	@echo "Make sure you have DOOM installed and running!"
	@echo "Example: chocolate-doom -window -geometry 640x480"

# Stop DOOM
doom-stop:
	@pkill -f doom || true

# Submit a DOOM command
cmd-%:
	@echo "$*" | nc localhost 9999

# Help
help:
	@echo "DOOM-COBOL Control System"
	@echo "========================"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start the entire system"
	@echo "  make down     - Stop the system"
	@echo "  make clean    - Clean up everything"
	@echo ""
	@echo "Operation Commands:"
	@echo "  make logs     - View all logs"
	@echo "  make logs-X   - View logs for service X (mainframe, bridge, etc)"
	@echo "  make test     - Run basic tests"
	@echo "  make cmd-X    - Send command X to DOOM (e.g., make cmd-'MOVE FORWARD')"
	@echo ""
	@echo "DOOM Commands (via telnet localhost 9999):"
	@echo "  MOVE FORWARD|BACK|LEFT|RIGHT [duration]"
	@echo "  TURN LEFT|RIGHT [degrees]"
	@echo "  SHOOT [count]"
	@echo "  USE"
	@echo "  WEAPON [1-7]"
	@echo "  STATUS"
	@echo "  RUN jobname"
	@echo ""
	@echo "Examples:"
	@echo "  echo 'MOVE FORWARD 2' | nc localhost 9999"
	@echo "  echo 'TURN RIGHT 90' | nc localhost 9999"
	@echo "  echo 'SHOOT 3' | nc localhost 9999"