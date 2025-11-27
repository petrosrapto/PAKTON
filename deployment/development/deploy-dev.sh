#!/bin/bash

# Description: 
#     Deployment script for PAKTON dev environment on EC2.
#     Manages Docker containers, environment variables, and service orchestration.
#     
# Author: Raptopoulos Petros [petrosrapto@gmail.com]
# Date  : 2025/11/24

set -e

echo "🚀 Starting PAKTON dev deployment..."

# Configuration
DEPLOY_DIR="/home/$(whoami)/pakton-dev"
REGISTRY="ghcr.io"
REPO_NAME="${GITHUB_REPOSITORY:-petrosrapto/pakton}"  # Lowercase repo name
BRANCH_NAME="${BRANCH_NAME:-develop}"  # Default to develop if not set
ENV_DIR="$DEPLOY_DIR/deployment/env"
COMPOSE_FILE="$DEPLOY_DIR/deployment/development/docker-compose.dev.yml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Docker Compose version and use V2 if available
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    log_info "Using Docker Compose V2"
else
    COMPOSE_CMD="docker-compose"
    log_warn "Using Docker Compose V1 (consider upgrading to V2)"
fi

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p "$ENV_DIR"
mkdir -p "$DEPLOY_DIR/logs"
mkdir -p "$DEPLOY_DIR/data/postgres"

# Stop existing containers
log_info "Stopping existing containers..."
cd "$DEPLOY_DIR"
$COMPOSE_CMD -f "$COMPOSE_FILE" down --remove-orphans || true

# Clean up Docker resources to free space
log_info "Cleaning up Docker resources..."
docker system prune -a --volumes -f
docker image prune -a -f

# Copy environment files from secure location
log_info "Setting up environment variables..."

# API environment files will be mounted into containers
# Frontend env variables are baked into the Docker image at build time (no runtime files needed)
log_info "Environment files prepared for container mounting"

# Export environment variables for docker-compose
export REGISTRY
export REPO_NAME
export BRANCH_NAME
export ENV_DIR
export DEPLOY_DIR

# Start services using the docker-compose file
log_info "Starting services..."
cd "$DEPLOY_DIR"
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d

# Wait for API to be ready
log_info "Waiting for API to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:5001/health > /dev/null 2>&1; then
        log_info "API is ready!"
        break
    fi
    attempt=$((attempt + 1))
    log_warn "Waiting for API... ($attempt/$max_attempts)"
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    log_error "API failed to start"
    $COMPOSE_CMD -f "$COMPOSE_FILE" logs multiagentframework_service
    exit 1
fi

# Wait for Frontend to be ready
log_info "Waiting for Frontend to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_info "Frontend is ready!"
        break
    fi
    attempt=$((attempt + 1))
    log_warn "Waiting for Frontend... ($attempt/$max_attempts)"
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    log_error "Frontend failed to start"
    $COMPOSE_CMD -f "$COMPOSE_FILE" logs web-app
    exit 1
fi

# Show running containers
log_info "Deployment complete! Running containers:"
docker ps | grep pakton-dev

# Save deployment log
log_info "Saving deployment log..."
echo "Deployment completed at $(date)" >> "$DEPLOY_DIR/logs/deployment.log"
echo "Commit: $(git rev-parse HEAD)" >> "$DEPLOY_DIR/logs/deployment.log"
echo "---" >> "$DEPLOY_DIR/logs/deployment.log"

log_info "✅ PAKTON dev deployment successful!"
log_info "Services running on localhost ports:"
log_info "  - API: http://localhost:5001"
log_info "  - Frontend: http://localhost:3000"
log_info "  - RabbitMQ Management: http://localhost:15672"
log_info ""
log_info "Add these to your Nginx configuration to expose via domain."
log_info "See: deployment/nginx/host-nginx-config.conf"
