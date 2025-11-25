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
$COMPOSE_CMD -f docker-compose.dev.yml down --remove-orphans || true

# Clean up Docker resources to free space
log_info "Cleaning up Docker resources..."
docker system prune -a --volumes -f
docker image prune -a -f

# Copy environment files from secure location
log_info "Setting up environment variables..."

# API environment files will be mounted into containers
# Frontend env variables are baked into the Docker image at build time (no runtime files needed)
log_info "Environment files prepared for container mounting"

# Update docker-compose to use pulled images
log_info "Starting services..."
cd "$DEPLOY_DIR"

# Create master docker-compose that orchestrates all services
cat > docker-compose.dev.yml <<EOF
version: "3.8"

services:
  rabbitmq:
    image: rabbitmq:3-management
    container_name: pakton-dev-rabbitmq
    ports:
      - "15672:15672"
    restart: always
    networks:
      - pakton-dev-network

  redis:
    image: redis:latest
    container_name: pakton-dev-redis
    restart: always
    networks:
      - pakton-dev-network

  postgres:
    image: postgres:15-alpine
    container_name: pakton-dev-postgres
    env_file:
      - $ENV_DIR/api.env
    volumes:
      - $DEPLOY_DIR/data/postgres:/var/lib/postgresql/data
    restart: always
    networks:
      - pakton-dev-network

  multiagentframework_service:
    image: ${REGISTRY}/${REPO_NAME}/pakton-api:${BRANCH_NAME}
    container_name: pakton-dev-api
    depends_on:
      - rabbitmq
      - redis
      - postgres
    env_file:
      - $ENV_DIR/api.env
    environment:
      CELERY_BROKER_URL: "amqp://rabbitmq:5672"
      CELERY_RESULT_BACKEND: "redis://redis:6379/0"
      SERVICE_NAME: "multiagentframework_service"
      PYTHONUNBUFFERED: "1"
    ports:
      - "5001:5001"
    restart: always
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
      - $ENV_DIR/archivist.env:/app/API/archivist.env:ro
      - $ENV_DIR/researcher.env:/app/API/researcher.env:ro
      - $ENV_DIR/interrogator.env:/app/API/interrogator.env:ro
    networks:
      - pakton-dev-network

  multiagentframework_worker:
    image: ${REGISTRY}/${REPO_NAME}/pakton-api:${BRANCH_NAME}
    container_name: pakton-dev-worker
    depends_on:
      - multiagentframework_service
      - rabbitmq
      - redis
      - postgres
    working_dir: /app
    command: [
      "celery",
      "-A", "API.tasks.celery_app",
      "worker",
      "-Q", "multiagentframework_service_queue",
      "--concurrency=4",
      "--loglevel=debug"
    ]
    env_file:
      - $ENV_DIR/api.env
    environment:
      CELERY_BROKER_URL: "amqp://rabbitmq:5672"
      CELERY_RESULT_BACKEND: "redis://redis:6379/0"
      SERVICE_NAME: "multiagentframework_service"
      PYTHONUNBUFFERED: "1"
    restart: always
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
      - $ENV_DIR/archivist.env:/app/API/archivist.env:ro
      - $ENV_DIR/researcher.env:/app/API/researcher.env:ro
      - $ENV_DIR/interrogator.env:/app/API/interrogator.env:ro
    networks:
      - pakton-dev-network

  web-app:
    image: ${REGISTRY}/${REPO_NAME}/pakton-frontend:${BRANCH_NAME}
    container_name: pakton-dev-frontend
    volumes:
      - $ENV_DIR/frontend.env:/app/.env:ro
    ports:
      - "3000:3000"
    restart: unless-stopped
    networks:
      - pakton-dev-network

networks:
  pakton-dev-network:
    driver: bridge
EOF

$COMPOSE_CMD -f docker-compose.dev.yml up -d

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
    $COMPOSE_CMD -f docker-compose.dev.yml logs multiagentframework_service
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
    $COMPOSE_CMD -f docker-compose.dev.yml logs web-app
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
