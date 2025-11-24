#!/bin/bash

# Description: 
#     EC2 instance setup script for PAKTON dev environment.
#     Run this script on a fresh EC2 instance to prepare it for deployments.
#     
# Author: Raptopoulos Petros [petrosrapto@gmail.com]
# Date  : 2025/11/24
#
# Usage: 
#     bash setup-ec2.sh <github-username> <repository-name>
#     Example: bash setup-ec2.sh petrosrapto PAKTON

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check arguments
if [ $# -lt 2 ]; then
    log_error "Usage: $0 <github-username> <repository-name>"
    log_error "Example: $0 petrosrapto PAKTON"
    exit 1
fi

GITHUB_USER=$1
REPO_NAME=$2
DEPLOY_DIR="$HOME/pakton-dev"

log_info "🚀 Setting up PAKTON dev environment on EC2"
log_info "GitHub User: $GITHUB_USER"
log_info "Repository: $REPO_NAME"
log_info "Deploy Directory: $DEPLOY_DIR"
echo ""

# Update system
log_step "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
log_step "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    log_info "Docker installed successfully"
else
    log_info "Docker already installed"
fi

# Install Docker Compose
log_step "Installing Docker Compose..."
if ! command -v docker compose &> /dev/null; then
    sudo apt install docker-compose-plugin -y
    log_info "Docker Compose installed successfully"
else
    log_info "Docker Compose already installed"
fi

# Install Git
log_step "Installing Git..."
if ! command -v git &> /dev/null; then
    sudo apt install git -y
    log_info "Git installed successfully"
else
    log_info "Git already installed"
fi

# Install utilities
log_step "Installing utilities..."
sudo apt install curl wget vim htop tree jq -y

# Create deployment directory
log_step "Creating deployment directory..."
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Clone repository
log_step "Cloning repository..."
if [ ! -d ".git" ]; then
    git clone "https://github.com/$GITHUB_USER/$REPO_NAME.git" .
    log_info "Repository cloned successfully"
else
    log_info "Repository already exists, pulling latest changes..."
    git pull
fi

# Checkout develop branch
log_step "Checking out develop branch..."
git checkout develop

# Create directory structure
log_step "Creating directory structure..."
mkdir -p deployment/env
mkdir -p deployment/nginx
mkdir -p deployment/scripts
mkdir -p logs
mkdir -p data/postgres

# Generate SSH key for GitHub Actions
log_step "Generating SSH key for GitHub Actions..."
if [ ! -f "$HOME/.ssh/github_actions_dev" ]; then
    ssh-keygen -t ed25519 -C "github-actions-dev" -f "$HOME/.ssh/github_actions_dev" -N ""
    cat "$HOME/.ssh/github_actions_dev.pub" >> "$HOME/.ssh/authorized_keys"
    chmod 600 "$HOME/.ssh/authorized_keys"
    log_info "SSH key generated successfully"
else
    log_info "SSH key already exists"
fi

# Get EC2 public IP
EC2_IP=$(curl -s http://checkip.amazonaws.com)

# Configure firewall (if UFW is installed)
if command -v ufw &> /dev/null; then
    log_step "Configuring firewall..."
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow OpenSSH
    sudo ufw --force enable
    log_info "Firewall configured successfully"
fi

# Docker group activation (requires logout/login)
log_step "Activating Docker group..."
newgrp docker << END
docker --version
END

# Create .gitignore for env files
log_step "Creating .gitignore for env files..."
cat > deployment/env/.gitignore << 'EOF'
*.env
!.gitignore
EOF

# Display setup summary
echo ""
log_info "✅ EC2 instance setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Add this SSH private key to GitHub Secrets as DEV_EC2_SSH_KEY:"
echo ""
cat "$HOME/.ssh/github_actions_dev"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "2. Add these GitHub Secrets:"
echo "   - DEV_EC2_HOST: $EC2_IP"
echo "   - DEV_EC2_USER: $USER"
echo "   - DEV_EC2_PORT: 22"
echo ""
echo "3. Add all other required secrets (see deployment/GITHUB_SECRETS.md)"
echo ""
echo "4. (Optional) Create environment files manually:"
echo "   cd $DEPLOY_DIR/deployment/env"
echo "   # Create: api.env, archivist.env, researcher.env, interrogator.env, frontend.env"
echo ""
echo "5. Test manual deployment:"
echo "   cd $DEPLOY_DIR"
echo "   bash deployment/deploy-dev.sh"
echo ""
echo "6. Push to develop branch to trigger automatic deployment"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Service URLs (after deployment):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "All Services:  http://$EC2_IP"
echo "API Endpoint:  http://$EC2_IP/api"
echo "Health Check:  http://$EC2_IP/health"
echo "RabbitMQ UI:   http://$EC2_IP/rabbitmq"
echo ""
echo "Note: Nginx runs as a Docker container, not on the host."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log_warn "IMPORTANT: You may need to logout and login again for Docker group changes to take effect"
log_warn "Or run: newgrp docker"
echo ""
