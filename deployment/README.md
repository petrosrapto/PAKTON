# PAKTON Deployment

This directory contains deployment configurations and scripts for PAKTON's CI/CD pipelines.

## 📁 Directory Structure

```
deployment/
├── README.md                    # This file - deployment overview
├── GITHUB_SECRETS.md           # GitHub Secrets reference
├── deploy-dev.sh               # Dev deployment script (runs on EC2)
├── nginx/
│   ├── SETUP_GUIDE.md         # Complete nginx, SSL, and DNS setup
│   ├── dev.pakton.site        # Dev nginx config
│   ├── pakton.site            # Production nginx config
│   └── nginx.conf             # Main nginx configuration
├── scripts/
│   └── create-env-files.sh    # Environment file creation from secrets
└── env/                        # Environment files (git-ignored)
    └── .gitignore
```

## 🚀 Quick Start

### Prerequisites

1. **EC2 Instance** running Ubuntu 22.04 LTS (t3.large or larger)
2. **Docker and Docker Compose** installed on EC2
3. **GitHub Secrets** configured (see [GITHUB_SECRETS.md](GITHUB_SECRETS.md))
4. **Nginx, DNS, and SSL** set up (see [nginx/SETUP_GUIDE.md](nginx/SETUP_GUIDE.md))

### Deploy

Push to the `develop` or `feature/PAKTON_backend` branch:

```bash
git push origin develop
```

GitHub Actions automatically:
1. Builds Docker images for API and Frontend
2. Pushes to GitHub Container Registry
3. SSHs into EC2 and deploys
4. Verifies services are healthy

**Production**: `https://pakton.site`  
**Development**: `https://dev.pakton.site`

## 📚 Documentation

- **[GITHUB_SECRETS.md](GITHUB_SECRETS.md)** - Required GitHub Secrets
- **[nginx/SETUP_GUIDE.md](nginx/SETUP_GUIDE.md)** - Nginx, SSL, and DNS setup

## 🔄 CI/CD Workflow

### Development Environment

**Trigger**: Push to `develop` or `feature/PAKTON_backend` branch

**Workflow**: `.github/workflows/deploy-dev.yml`

**Process**:
1. Build API Docker image (`PAKTON Framework/API/Dockerfile`)
2. Build Frontend Docker image (`PAKTON Framework/Frontend/v0.2/Dockerfile`)
3. Push to GitHub Container Registry (`ghcr.io/petrosrapto/pakton/*`)
4. SSH to EC2 instance
5. Pull latest images with branch-based tags
6. Create environment files from GitHub Secrets
7. Run `deploy-dev.sh` script
8. Health checks (API: `/health`, Frontend: `/`)

**Deployment URL**: `https://dev.pakton.site`

### Production Environment

**Deployment URL**: `https://pakton.site`

(Uses same infrastructure, different services on different ports)

## 🔧 Scripts

### `create-env-files.sh`

**Purpose**: Create environment files from GitHub Secrets

**Usage**:
```bash
bash create-env-files.sh <env-directory>
```

**What it does**:
- Reads environment variables passed from GitHub Actions
- Creates .env files for all services
- Sets appropriate file permissions

**Note**: This script runs automatically during GitHub Actions deployment.

### `deploy-dev.sh`

**Purpose**: Deploy PAKTON services on EC2

**Usage**:
```bash
bash deploy-dev.sh
```

**What it does**:
- Stops existing containers
- Creates dev-specific docker-compose files
- Copies environment files to appropriate locations
- Starts all services (API, Frontend, RabbitMQ, Redis, PostgreSQL)
- Waits for services to be healthy
- Logs deployment details

**Note**: This script runs automatically during GitHub Actions deployment.

## 🔐 Environment Variables

Environment variables are managed through GitHub Secrets and automatically deployed to EC2.

### Required Environment Files

1. **`api.env`** - API service configuration
2. **`archivist.env`** - Archivist agent configuration
3. **`researcher.env`** - Researcher agent configuration
4. **`interrogator.env`** - Interrogator agent configuration
5. **`frontend.env`** - Frontend application configuration

See [GITHUB_SECRETS.md](GITHUB_SECRETS.md) for complete list of required secrets.

## 🌐 Nginx Configuration

### Dev Environment

- **Location**: `nginx/dev.conf`
- **Routes**:
  - `/` → Frontend (port 3000)
  - `/api/*` → API (port 5001)
  - `/rabbitmq/*` → RabbitMQ Management (port 15672)
  - `/health` → Health check endpoint

### Features

- Rate limiting on API endpoints
- SSE/Streaming support for long-running queries
- CORS headers configured
- Reverse proxy for all services
- Optional HTTPS configuration (commented out for dev)

## 🐳 Docker Architecture

### Development Containers

1. **pakton-dev-api** - FastAPI service (port 5001)
2. **pakton-dev-worker** - Celery worker
3. **pakton-dev-frontend** - Next.js app (port 3000)
4. **pakton-dev-postgres** - PostgreSQL database
5. **pakton-dev-rabbitmq** - Message broker
6. **pakton-dev-redis** - Result backend

**Note**: Services run on localhost ports, reverse-proxied by nginx to `https://dev.pakton.site`

### Host Nginx

Nginx runs on the host (not containerized) and proxies:
- `pakton.site` → Production services (ports 8501, 3001, 8502)
- `dev.pakton.site` → Development frontend (port 3000)

### Networks

- **pakton-dev-network** - Docker bridge network

### Volumes

- **postgres_data** - Persistent PostgreSQL data
- **rabbitmq_data** - Persistent message queue data

## 🔍 Monitoring & Debugging

### Check Container Status

```bash
docker ps | grep pakton-dev
```

### View Logs

```bash
# API logs
docker logs -f pakton-dev-api

# Worker logs
docker logs -f pakton-dev-worker

# Frontend logs
docker logs -f pakton-dev-frontend

# All logs
docker-compose -f docker-compose.dev.yml logs -f
```

### Check Health

```bash
# API health
curl http://localhost:5001/health

# Frontend
curl http://localhost:3000

# Full system status
docker ps
docker stats
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it pakton-dev-postgres psql -U pakton_user -d pakton_dev
```

## 🛠️ Troubleshooting

### Deployment Fails

1. Check GitHub Actions logs
2. SSH into EC2 and check `/home/ubuntu/pakton-dev/logs/deployment.log`
3. Verify all GitHub Secrets are set correctly
4. Check Docker container logs

### Services Won't Start

```bash
# Check Docker service
sudo systemctl status docker

# Check disk space
df -h

# Check Docker resources
docker system df

# Clean up
docker system prune -a
```

### Nginx Issues

```bash
# Check status
sudo systemctl status nginx

# Test config
sudo nginx -t

# View logs
sudo tail -f /var/log/nginx/dev.pakton.site.error.log
sudo tail -f /var/log/nginx/pakton.site.error.log

# Reload
sudo systemctl reload nginx
```

For complete nginx setup, see [nginx/SETUP_GUIDE.md](nginx/SETUP_GUIDE.md)

### Database Connection Issues

```bash
# Check PostgreSQL container
docker logs pakton-dev-postgres

# Verify environment variables
docker exec pakton-dev-api env | grep POSTGRES

# Test connection
docker exec pakton-dev-api psql -h postgres -U pakton_user -d pakton_dev
```

## 📊 Deployment Checklist

- [ ] EC2 instance launched and configured
- [ ] Security groups allow ports 22, 80, 443
- [ ] Setup script executed successfully
- [ ] SSH key added to GitHub Secrets
- [ ] All required GitHub Secrets configured
- [ ] Nginx configured and running
- [ ] Domain/DNS configured (optional)
- [ ] SSL certificate installed (optional for dev)
- [ ] Test deployment successful
- [ ] Services accessible via public URL
- [ ] Monitoring configured

## 🔄 Update Procedures

### Update Dependencies

```bash
# Pull latest code
git pull origin develop

# Rebuild containers
docker-compose -f docker-compose.dev.yml up -d --build
```

### Update Nginx Configuration

```bash
# Update config
sudo nano /etc/nginx/sites-available/pakton-dev

# Test
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

### Update Environment Variables

Option 1: Update GitHub Secrets and redeploy

Option 2: Update files manually on EC2:
```bash
cd ~/pakton-dev/deployment/env
nano api.env  # Edit as needed
bash ~/pakton-dev/deployment/deploy-dev.sh
```



## 📞 Support

For issues:
1. Check GitHub Actions logs in the Actions tab
2. SSH to EC2 and check `/home/ubuntu/pakton-dev/logs/deployment.log`
3. Review [nginx/SETUP_GUIDE.md](nginx/SETUP_GUIDE.md) for infrastructure setup
4. Check [GITHUB_SECRETS.md](GITHUB_SECRETS.md) for required secrets

---

**Last Updated**: November 25, 2025
