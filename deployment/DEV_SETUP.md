# PAKTON Dev Environment Setup Guide

This guide will help you set up the development environment for PAKTON on AWS EC2 with automated deployment via GitHub Actions.

## Table of Contents
1. [EC2 Instance Setup](#ec2-instance-setup)
2. [GitHub Secrets Configuration](#github-secrets-configuration)
3. [Environment Variables Setup](#environment-variables-setup)
4. [Nginx Configuration](#nginx-configuration)
5. [Initial Deployment](#initial-deployment)
6. [Troubleshooting](#troubleshooting)

---

## EC2 Instance Setup

### 1. Launch EC2 Instance

**Recommended Specifications:**
- Instance Type: `t3.large` or larger (minimum 2 vCPU, 8GB RAM)
- OS: Ubuntu 22.04 LTS
- Storage: 30GB+ SSD
- Security Group: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS)

### 2. Connect to EC2 Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 3. Install Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Install Git
sudo apt install git -y

# Install other utilities
sudo apt install curl wget vim htop -y
```

**Note**: Nginx runs as a Docker container, not installed on the host.

### 4. Setup Deployment Directory

```bash
# Create deployment directory
mkdir -p ~/pakton-dev
cd ~/pakton-dev

# Clone the repository
git clone https://github.com/petrosrapto/PAKTON.git .
git checkout develop

# Create directory structure
mkdir -p deployment/env
mkdir -p deployment/nginx
mkdir -p logs
mkdir -p data/postgres

# Make deployment script executable
chmod +x deployment/deploy-dev.sh
```

### 5. Generate SSH Key for GitHub Actions

```bash
# Generate SSH key (don't set a passphrase)
ssh-keygen -t ed25519 -C "github-actions-dev" -f ~/.ssh/github_actions_dev

# Add to authorized_keys
cat ~/.ssh/github_actions_dev.pub >> ~/.ssh/authorized_keys

# Display private key (you'll add this to GitHub Secrets)
cat ~/.ssh/github_actions_dev
```

---

## GitHub Secrets Configuration

Navigate to your GitHub repository: **Settings → Secrets and variables → Actions → New repository secret**

### Required Secrets

#### 1. EC2 Connection Secrets

| Secret Name | Description | Example |
|------------|-------------|---------|
| `DEV_EC2_HOST` | EC2 instance public IP or domain | `54.123.45.67` |
| `DEV_EC2_USER` | SSH username | `ubuntu` |
| `DEV_EC2_SSH_KEY` | Private SSH key generated above | Contents of `~/.ssh/github_actions_dev` |
| `DEV_EC2_PORT` | SSH port (optional, defaults to 22) | `22` |

#### 2. API Environment Variables

| Secret Name | Description | Required |
|------------|-------------|----------|
| `DEV_SUPABASE_URL` | Supabase project URL | Yes |
| `DEV_SUPABASE_JWT_SECRET` | Supabase JWT secret | Yes |
| `DEV_POSTGRES_DB` | PostgreSQL database name | Yes |
| `DEV_POSTGRES_USER` | PostgreSQL username | Yes |
| `DEV_POSTGRES_PASSWORD` | PostgreSQL password | Yes |
| `DEV_ENABLE_AUTHENTICATION` | Enable auth (true/false) | Yes |

#### 3. AI/ML Service API Keys

| Secret Name | Description | Required |
|------------|-------------|----------|
| `DEV_OPENAI_API_KEY` | OpenAI API key | Yes |
| `DEV_HUGGINGFACE_TOKEN` | HuggingFace token | Yes |
| `DEV_EMBEDDINGS_API_KEY` | Embeddings API key | Yes |
| `DEV_TAVILY_API_KEY` | Tavily API key | Yes |
| `DEV_LANGCHAIN_API_KEY` | LangSmith API key | Optional |
| `DEV_PINECONE_API_KEY` | Pinecone API key | Yes |
| `DEV_GOOGLE_API_KEY` | Google API key | Optional |

#### 4. AWS Configuration

| Secret Name | Description | Required |
|------------|-------------|----------|
| `DEV_AWS_ACCESS_KEY_ID` | AWS access key | Yes |
| `DEV_AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes |
| `DEV_AWS_REGION_NAME` | AWS region | Yes |

#### 5. Frontend Environment Variables

| Secret Name | Description | Required |
|------------|-------------|----------|
| `DEV_NEXT_PUBLIC_SUPABASE_URL` | Supabase URL (public) | Yes |
| `DEV_NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key | Yes |
| `DEV_NEXT_PUBLIC_SUPABASE_URL_DOCUMENTS` | Supabase docs URL | Yes |
| `DEV_NEXT_PUBLIC_SUPABASE_ANON_KEY_DOCUMENTS` | Supabase docs key | Yes |
| `DEV_NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth client ID | Optional |
| `DEV_LOCAL_DEVELOPMENT` | Set to "true" for dev | Yes |

---

## Environment Variables Setup

### Create Environment Files on EC2

SSH into your EC2 instance and create the environment files:

```bash
cd ~/pakton-dev/deployment/env
```

#### 1. API Environment (`api.env`)

```bash
cat > api.env << 'EOF'
# Supabase Configuration
SUPABASE_URL=your-supabase-url
SUPABASE_JWT_SECRET=your-jwt-secret

# Authentication
ENABLE_AUTHENTICATION=true

# PostgreSQL
POSTGRES_DB=pakton_dev
POSTGRES_USER=pakton_user
POSTGRES_PASSWORD=your-secure-password
EOF
```

#### 2. Archivist Environment (`archivist.env`)

```bash
cat > archivist.env << 'EOF'
# HuggingFace
HUGGINGFACE_TOKEN=your-token

# AWS
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION_NAME=us-west-2

# OpenAI
EMBEDDINGS_API_KEY=your-key
OPENAI_API_KEY=your-key

# Tavily
TAVILY_API_KEY=your-key

# LangChain
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=pakton-dev
LANGCHAIN_API_KEY=your-key
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_VERBOSE=true

# Pinecone
PINECONE_API_KEY=your-key
EOF
```

#### 3. Researcher Environment (`researcher.env`)

Copy from archivist.env and add Google API key if needed:

```bash
cp archivist.env researcher.env
echo "GOOGLE_API_KEY=your-google-key" >> researcher.env
```

#### 4. Interrogator Environment (`interrogator.env`)

```bash
cp archivist.env interrogator.env
echo "GOOGLE_API_KEY=your-google-key" >> interrogator.env
echo "HUGGINGFACEHUB_API_TOKEN=your-token" >> interrogator.env
```

#### 5. Frontend Environment (`frontend.env`)

```bash
cat > frontend.env << 'EOF'
# Development Flag
LOCAL_DEVELOPMENT=true

# Supabase Auth
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Supabase Documents
NEXT_PUBLIC_SUPABASE_URL_DOCUMENTS=your-docs-url
NEXT_PUBLIC_SUPABASE_ANON_KEY_DOCUMENTS=your-docs-key

# Google OAuth
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-client-id
EOF
```

### Secure the Environment Files

```bash
chmod 600 ~/pakton-dev/deployment/env/*
```

---

## Nginx Configuration

**Nginx runs as a Docker container** - no manual configuration needed!

The deployment script automatically:
- Builds the Nginx container from `deployment/nginx/Dockerfile`
- Uses the configuration from `deployment/nginx/nginx.conf`
- Exposes port 80 on the host
- Connects to all services via Docker network

### Configure Firewall (if using UFW)

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow OpenSSH
sudo ufw enable
```

### Optional: Setup SSL with Let's Encrypt

For SSL, you'll need to update the Nginx Dockerfile and configuration:

1. Mount Let's Encrypt certificates into the Nginx container
2. Update nginx.conf to use SSL
3. Expose port 443 in docker-compose

See production setup guide for SSL configuration details.

---

## Initial Deployment

### 1. Update GitHub Repository Name

Edit the deployment script to include your actual repository name:

```bash
nano ~/pakton-dev/deployment/deploy-dev.sh
# Update: REPO_NAME="petrosrapto/pakton"
```

### 2. Test Manual Deployment

```bash
cd ~/pakton-dev
bash deployment/deploy-dev.sh
```

### 3. Verify Services

```bash
# Check running containers
docker ps

# Check API health
curl http://localhost:5001/health

# Check Frontend
curl http://localhost:3000

# Check logs
docker logs pakton-dev-api
docker logs pakton-dev-frontend
```

### 4. Trigger GitHub Actions

Push a commit to the `develop` branch:

```bash
git checkout develop
git commit --allow-empty -m "Test dev deployment"
git push origin develop
```

Monitor the deployment in GitHub Actions tab of your repository.

---

## Troubleshooting

### Check Container Logs

```bash
# API logs
docker logs -f pakton-dev-api

# Worker logs
docker logs -f pakton-dev-worker

# Frontend logs
docker logs -f pakton-dev-frontend

# PostgreSQL logs
docker logs -f pakton-dev-postgres
```

### Check Nginx Logs

```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

### Restart Services

```bash
# Restart all containers
cd ~/pakton-dev/PAKTON\ Framework/API
docker-compose -f docker-compose.dev.yml restart

# Restart Nginx
sudo systemctl restart nginx
```

### Check Disk Space

```bash
df -h
docker system df
```

### Clean Up Docker Resources

```bash
# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# Full cleanup (careful!)
docker system prune -a --volumes -f
```

### SSH Connection Issues

```bash
# Test SSH from local machine
ssh -i your-key.pem -v ubuntu@your-ec2-ip

# Check SSH on EC2
sudo systemctl status ssh
sudo tail -f /var/log/auth.log
```

### Database Issues

```bash
# Access PostgreSQL
docker exec -it pakton-dev-postgres psql -U pakton_user -d pakton_dev

# Check database size
docker exec pakton-dev-postgres psql -U pakton_user -d pakton_dev -c "SELECT pg_size_pretty(pg_database_size('pakton_dev'));"
```

---

## Monitoring

### Setup Basic Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop -y

# Monitor system resources
htop

# Monitor Docker stats
docker stats
```

### Check Application Metrics

```bash
# API metrics (if endpoint exists)
curl http://localhost:5001/metrics

# RabbitMQ Management UI
# Access: http://your-ec2-ip:15672
# Default credentials: guest/guest
```

---

## Next Steps

1. **Set up production environment** following similar steps
2. **Configure production pipeline** for main branch and release tags
3. **Set up monitoring and alerting** (CloudWatch, Datadog, etc.)
4. **Configure automated backups** for PostgreSQL
5. **Set up log aggregation** (CloudWatch Logs, ELK stack, etc.)

---

## Security Checklist

- [ ] SSH key-based authentication only (disable password auth)
- [ ] Firewall configured (UFW or Security Groups)
- [ ] Environment files secured (600 permissions)
- [ ] SSL certificate installed (Let's Encrypt)
- [ ] RabbitMQ management UI secured or firewalled
- [ ] PostgreSQL not exposed to public internet
- [ ] Regular security updates enabled
- [ ] Secrets rotated periodically
- [ ] Docker images from trusted sources only
- [ ] Rate limiting configured in Nginx

---

## Support

For issues or questions:
- Check GitHub Issues
- Review deployment logs: `~/pakton-dev/logs/deployment.log`
- Contact: petrosrapto@gmail.com
