#!/bin/bash

# Database Migration Helper Script
# This script helps manage Alembic database migrations for the PAKTON API

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}PAKTON Database Migration Helper${NC}"
echo "=================================="

# Change to API directory
cd "$(dirname "$0")"

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo -e "${RED}Error: Alembic is not installed${NC}"
    echo "Please install dependencies: pip install -r requirements.txt"
    exit 1
fi

# Function to show usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  init        - Initialize database (first time setup)"
    echo "  upgrade     - Apply all pending migrations"
    echo "  downgrade   - Rollback last migration"
    echo "  current     - Show current migration version"
    echo "  history     - Show migration history"
    echo "  create      - Create a new migration (auto-generate)"
    echo "  help        - Show this help message"
    echo ""
}

# Parse command
COMMAND=${1:-help}

case $COMMAND in
    init)
        echo -e "${YELLOW}Initializing database...${NC}"
        echo "This will create all tables defined in the initial migration."
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            alembic upgrade head
            echo -e "${GREEN}Database initialized successfully!${NC}"
        else
            echo "Cancelled."
        fi
        ;;
    
    upgrade)
        echo -e "${YELLOW}Applying pending migrations...${NC}"
        alembic upgrade head
        echo -e "${GREEN}Migrations applied successfully!${NC}"
        ;;
    
    downgrade)
        echo -e "${YELLOW}Rolling back last migration...${NC}"
        read -p "Are you sure? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            alembic downgrade -1
            echo -e "${GREEN}Migration rolled back successfully!${NC}"
        else
            echo "Cancelled."
        fi
        ;;
    
    current)
        echo -e "${YELLOW}Current migration version:${NC}"
        alembic current
        ;;
    
    history)
        echo -e "${YELLOW}Migration history:${NC}"
        alembic history --verbose
        ;;
    
    create)
        echo -e "${YELLOW}Creating new migration...${NC}"
        read -p "Enter migration description: " DESCRIPTION
        if [ -z "$DESCRIPTION" ]; then
            echo -e "${RED}Error: Description cannot be empty${NC}"
            exit 1
        fi
        alembic revision --autogenerate -m "$DESCRIPTION"
        echo -e "${GREEN}Migration created successfully!${NC}"
        echo -e "${YELLOW}Please review the migration file before applying.${NC}"
        ;;
    
    help)
        usage
        ;;
    
    *)
        echo -e "${RED}Error: Unknown command '$COMMAND'${NC}"
        echo ""
        usage
        exit 1
        ;;
esac
