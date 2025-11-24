# PAKTON Deployment

This directory contains all deployment configurations and scripts for PAKTON's CI/CD pipelines.

## 📁 Directory Structure

```
deployment/
├── README.md                    # This file
├── DEV_SETUP.md                # Detailed dev environment setup guide
├── GITHUB_SECRETS.md           # GitHub Secrets reference
├── deploy-dev.sh               # Dev deployment script (runs on EC2)
├── nginx/
│   └── dev.conf               # Nginx configuration for dev environment
├── scripts/
│   ├── setup-ec2.sh           # EC2 initial setup script
│   └── create-env-files.sh    # Environment file creation script
└── env/                        # Environment files (git-ignored)
    ├── api.env
    ├── archivist.env
    ├── researcher.env
    ├── interrogator.env
    └── frontend.env
```

## 🚀 Quick Start

### For First-Time Setup

1. **Launch EC2 Instance**
   - Instance type: t3.large or larger
   - OS: Ubuntu 22.04 LTS
   - Storage: 30GB+ SSD
   - Open ports: 22, 80, 443

2. **Run Setup Script on EC2**
   ```bash
   # SSH into EC2
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Download and run setup script
   curl -o setup-ec2.sh https://raw.githubusercontent.com/petrosrapto/PAKTON/develop/deployment/scripts/setup-ec2.sh
   chmod +x setup-ec2.sh
   ./setup-ec2.sh petrosrapto PAKTON
   ```

3. **Configure GitHub Secrets**
   - Copy SSH private key shown at end of setup
   - Add all required secrets (see [GITHUB_SECRETS.md](GITHUB_SECRETS.md))

4. **Push to Develop Branch**
   ```bash
   git push origin develop
   ```
   
   GitHub Actions will automatically build and deploy!

### For Subsequent Deployments

Just push to the `develop` branch - GitHub Actions handles everything automatically.

## 📚 Documentation

- **[DEV_SETUP.md](DEV_SETUP.md)** - Complete development environment setup guide
- **[GITHUB_SECRETS.md](GITHUB_SECRETS.md)** - GitHub Secrets quick reference

## 🔄 CI/CD Workflows

### Development Environment (`develop` branch)

**Trigger**: Push to `develop` branch

**Workflow**: `.github/workflows/deploy-dev.yml`

**Steps**:
1. Build Docker images for API and Frontend
2. Push images to GitHub Container Registry
3. SSH into dev EC2 instance
4. Pull latest code and images
5. Create environment files from GitHub Secrets
6. Run deployment script
7. Verify services are healthy

**Deployment URL**: `http://your-dev-ec2-ip`

### Production Environment (Future)

**Trigger**: Release tags (e.g., `v1.0.0`)

**Workflow**: `.github/workflows/deploy-prod.yml` (to be created)

**Build Trigger**: Push to `main` branch (build only, no deploy)

**Deploy Trigger**: Release tag creation

## 🔧 Scripts

### `setup-ec2.sh`

**Purpose**: Initial EC2 instance setup

**Usage**:
```bash
bash setup-ec2.sh <github-username> <repo-name>
```

**What it does**:
- Installs Docker, Docker Compose, Nginx, Git
- Clones repository
- Creates directory structure
- Generates SSH keys for GitHub Actions
- Configures Nginx
- Sets up firewall

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

All containers use `pakton-dev-` prefix:

1. **pakton-dev-nginx** - Nginx reverse proxy (port 80)
2. **pakton-dev-api** - FastAPI service (internal)
3. **pakton-dev-worker** - Celery worker
4. **pakton-dev-frontend** - Next.js app (internal)
5. **pakton-dev-postgres** - PostgreSQL database (internal)
6. **pakton-dev-rabbitmq** - Message broker (internal)
7. **pakton-dev-redis** - Result backend (internal)

**Note**: Only Nginx exposes ports externally. All other services communicate via Docker network.

### Networks

- **pakton-dev-network** - Bridge network connecting all services

### Volumes

- **postgres_data** - Persistent PostgreSQL data
- **~/.cache/huggingface** - HuggingFace model cache (mounted)

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

### Access RabbitMQ Management

```bash
# Open in browser
http://your-ec2-ip:15672
# Default credentials: guest/guest
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
# Check Nginx status
sudo systemctl status nginx

# Test configuration
sudo nginx -t

# View error logs
sudo tail -f /var/log/nginx/error.log

# Reload Nginx
sudo systemctl reload nginx
```

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

## 🚀 Production Deployment (Coming Soon)

Production deployment will follow a similar pattern but with:

- Separate EC2 instance
- Different docker-compose configuration
- Production-grade security settings
- SSL/HTTPS enforced
- Automated backups
- Monitoring and alerting
- Deploy triggered by release tags only
- Build triggered by commits to `main` branch

---

## 📞 Support

For issues or questions:
- Check [DEV_SETUP.md](DEV_SETUP.md) for detailed setup instructions
- Review GitHub Actions logs
- Check deployment logs on EC2
- Contact: petrosrapto@gmail.com

---

**Last Updated**: November 24, 2025
