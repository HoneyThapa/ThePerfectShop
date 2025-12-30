#!/bin/bash

# ThePerfectShop Backend Deployment Script
# This script handles deployment for different environments

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="theperfectshop"
ENVIRONMENT="${ENVIRONMENT:-development}"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
ThePerfectShop Backend Deployment Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    start           Start all services
    stop            Stop all services
    restart         Restart all services
    build           Build Docker images
    logs            Show service logs
    status          Show service status
    clean           Clean up containers and volumes
    migrate         Run database migrations
    seed            Seed database with sample data
    backup          Backup database
    restore         Restore database from backup
    health          Check service health
    monitoring      Start with monitoring stack (Prometheus/Grafana)

Options:
    -e, --env       Environment (development|staging|production)
    -f, --file      Docker compose file to use
    -d, --detach    Run in detached mode
    -h, --help      Show this help message

Examples:
    $0 start -e production
    $0 logs api
    $0 migrate
    $0 monitoring
EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_warning ".env file not found. Creating from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "Please edit .env file with your configuration before proceeding."
        else
            log_error ".env.example file not found. Cannot create .env file."
            exit 1
        fi
    fi
    
    log_success "Prerequisites check completed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    log_success "Docker images built successfully"
}

# Start services
start_services() {
    local detach_flag=""
    if [ "$1" = "detach" ]; then
        detach_flag="-d"
    fi
    
    log_info "Starting ThePerfectShop services..."
    docker-compose -f $COMPOSE_FILE up $detach_flag
    
    if [ "$detach_flag" = "-d" ]; then
        log_success "Services started in detached mode"
        show_status
    fi
}

# Stop services
stop_services() {
    log_info "Stopping ThePerfectShop services..."
    docker-compose -f $COMPOSE_FILE down
    log_success "Services stopped"
}

# Restart services
restart_services() {
    log_info "Restarting ThePerfectShop services..."
    docker-compose -f $COMPOSE_FILE restart
    log_success "Services restarted"
}

# Show logs
show_logs() {
    local service="$1"
    if [ -n "$service" ]; then
        docker-compose -f $COMPOSE_FILE logs -f "$service"
    else
        docker-compose -f $COMPOSE_FILE logs -f
    fi
}

# Show status
show_status() {
    log_info "Service status:"
    docker-compose -f $COMPOSE_FILE ps
}

# Clean up
clean_up() {
    log_warning "This will remove all containers, networks, and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_info "Cleaning up..."
        docker-compose -f $COMPOSE_FILE down -v --remove-orphans
        docker system prune -f
        log_success "Cleanup completed"
    else
        log_info "Cleanup cancelled"
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U theperfectshop || {
        log_error "Database is not ready. Please start the services first."
        exit 1
    }
    
    # Run migrations
    docker-compose -f $COMPOSE_FILE exec -T api alembic upgrade head
    log_success "Database migrations completed"
}

# Check health
check_health() {
    log_info "Checking service health..."
    
    # Check API health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "API is healthy"
    else
        log_error "API is not responding"
    fi
    
    # Check database
    if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U theperfectshop > /dev/null 2>&1; then
        log_success "Database is healthy"
    else
        log_error "Database is not responding"
    fi
    
    # Check Redis
    if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is healthy"
    else
        log_error "Redis is not responding"
    fi
}

# Start with monitoring
start_monitoring() {
    log_info "Starting ThePerfectShop with monitoring stack..."
    docker-compose -f $COMPOSE_FILE --profile monitoring up -d
    log_success "Services with monitoring started"
    log_info "Grafana available at: http://localhost:3000 (admin/admin)"
    log_info "Prometheus available at: http://localhost:9091"
}

# Backup database
backup_database() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    log_info "Creating database backup: $backup_file"
    
    docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump -U theperfectshop theperfectshop > "$backup_file"
    log_success "Database backup created: $backup_file"
}

# Main script logic
main() {
    cd "$SCRIPT_DIR"
    
    # Parse command line arguments
    COMMAND=""
    DETACH=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -f|--file)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            -d|--detach)
                DETACH=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            start|stop|restart|build|logs|status|clean|migrate|health|monitoring|backup)
                COMMAND="$1"
                shift
                ;;
            *)
                if [ -z "$COMMAND" ]; then
                    log_error "Unknown command: $1"
                    show_help
                    exit 1
                fi
                break
                ;;
        esac
    done
    
    # Set environment-specific compose file
    if [ "$ENVIRONMENT" = "production" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    elif [ "$ENVIRONMENT" = "staging" ]; then
        COMPOSE_FILE="docker-compose.staging.yml"
    fi
    
    # Execute command
    case $COMMAND in
        start)
            check_prerequisites
            if [ "$DETACH" = true ]; then
                start_services "detach"
            else
                start_services
            fi
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        build)
            check_prerequisites
            build_images
            ;;
        logs)
            show_logs "$1"
            ;;
        status)
            show_status
            ;;
        clean)
            clean_up
            ;;
        migrate)
            run_migrations
            ;;
        health)
            check_health
            ;;
        monitoring)
            check_prerequisites
            start_monitoring
            ;;
        backup)
            backup_database
            ;;
        "")
            log_error "No command specified"
            show_help
            exit 1
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"