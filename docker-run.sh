#!/bin/bash

# Docker management script for Testing Agent

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default compose file
COMPOSE_FILE="docker-compose.yml"

# Check for production flag
if [[ "$*" == *"--prod"* ]]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    print_status() {
        echo -e "${BLUE}[PROD INFO]${NC} $1"
    }
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found."
        if [ -f "env.docker.example" ]; then
            print_status "Copying env.docker.example to .env..."
            cp env.docker.example .env
            print_warning "Please edit .env file with your configuration before proceeding."
            exit 1
        else
            print_error "No environment template found. Please create .env file."
            exit 1
        fi
    fi
}

# Function to create data directories
create_data_dirs() {
    print_status "Creating data directories..."
    mkdir -p data/{videos,screenshots,reports,logs}
    print_success "Data directories created."
}

# Function to build the Docker image
build() {
    print_status "Building Testing Agent Docker image..."
    docker-compose -f "$COMPOSE_FILE" build
    print_success "Docker image built successfully."
}

# Function to start the application
start() {
    print_status "Starting Testing Agent..."
    docker-compose -f "$COMPOSE_FILE" up -d
    print_success "Testing Agent started successfully."
    print_status "You can view logs with: ./docker-run.sh logs"
}

# Function to stop the application
stop() {
    print_status "Stopping Testing Agent..."
    docker-compose -f "$COMPOSE_FILE" down
    print_success "Testing Agent stopped."
}

# Function to restart the application
restart() {
    print_status "Restarting Testing Agent..."
    docker-compose -f "$COMPOSE_FILE" restart
    print_success "Testing Agent restarted."
}

# Function to view logs
logs() {
    print_status "Showing Testing Agent logs (Ctrl+C to exit)..."
    docker-compose -f "$COMPOSE_FILE" logs -f testing-agent
}

# Function to show status
status() {
    print_status "Testing Agent status:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    print_status "Container health:"
    CONTAINER_NAME="testing-agent"
    if [[ "$COMPOSE_FILE" == *"prod"* ]]; then
        CONTAINER_NAME="testing-agent-prod"
    fi
    docker inspect "$CONTAINER_NAME" --format='{{.State.Health.Status}}' 2>/dev/null || echo "Health check not available"
}

# Function to open shell in container
shell() {
    print_status "Opening shell in Testing Agent container..."
    docker-compose -f "$COMPOSE_FILE" exec testing-agent /bin/bash
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker-compose -f "$COMPOSE_FILE" down -v
    docker system prune -f
    print_success "Cleanup completed."
}

# Function to show help
show_help() {
    echo "Testing Agent Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build      Build the Docker image"
    echo "  start      Start the Testing Agent"
    echo "  stop       Stop the Testing Agent"
    echo "  restart    Restart the Testing Agent"
    echo "  logs       View application logs"
    echo "  status     Show application status"
    echo "  shell      Open shell in container"
    echo "  cleanup    Remove containers and volumes"
    echo "  help       Show this help message"
    echo ""
    echo "Options:"
    echo "  --prod     Use production Docker Compose configuration"
    echo ""
    echo "Examples:"
    echo "  $0 build && $0 start           # Build and start (development)"
    echo "  $0 start --prod                # Start in production mode"
    echo "  $0 logs                        # View logs"
    echo "  $0 status                      # Check status"
    echo "  $0 cleanup --prod              # Cleanup production deployment"
}

# Remove --prod flag from arguments and get command
COMMAND="${1:-help}"
if [ "$COMMAND" = "--prod" ]; then
    COMMAND="${2:-help}"
elif [ "$2" = "--prod" ]; then
    # Command is first, --prod is second
    true
fi

# Main script logic
case "$COMMAND" in
    "build")
        check_docker
        check_env_file
        create_data_dirs
        build
        ;;
    "start")
        check_docker
        check_env_file
        create_data_dirs
        start
        ;;
    "stop")
        check_docker
        stop
        ;;
    "restart")
        check_docker
        restart
        ;;
    "logs")
        check_docker
        logs
        ;;
    "status")
        check_docker
        status
        ;;
    "shell")
        check_docker
        shell
        ;;
    "cleanup")
        check_docker
        cleanup
        ;;
    "help"|*)
        show_help
        ;;
esac 