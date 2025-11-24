# PAKTON CI/CD Setup - Quick Start Guide

This guide will help you set up automated deployment for PAKTON in **under 30 minutes**.

## 🎯 What You'll Get

- ✅ Automated deployment to dev environment on every push to `develop` branch
- ✅ Docker-based deployment with all services orchestrated
- ✅ Nginx reverse proxy with rate limiting and SSE support
- ✅ Secure secret management via GitHub Secrets
- ✅ Health checks and automatic rollback on failure

## 📋 Prerequisites

- AWS account with EC2 access
- GitHub repository with the PAKTON code
- Basic familiarity with SSH and command line

## 🚀 5-Step Setup

### Step 1: Launch EC2 Instance (5 minutes)

1. **Go to AWS EC2 Console**
2. **Click "Launch Instance"**
3. **Configure**:
   - Name: `pakton-dev`
   - AMI: **Ubuntu 22.04 LTS**
   - Instance type: **t3.large** (or larger)
   - Create new key pair or use existing
   - Storage: **30 GB** gp3
   
4. **Configure Security Group**:
   - SSH (22) - Your IP or GitHub Actions IPs
   - HTTP (80) - Anywhere (0.0.0.0/0)
   - HTTPS (443) - Anywhere (0.0.0.0/0, if using SSL)
   
   **Note**: All other ports are internal to Docker - no need to expose them!

5. **Launch and note the Public IP**

### Step 2: Setup EC2 Instance (10 minutes)

```bash
# 1. SSH into your EC2 instance
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# 2. Download setup script
wget https://raw.githubusercontent.com/petrosrapto/PAKTON/develop/deployment/scripts/setup-ec2.sh

# 3. Make it executable
chmod +x setup-ec2.sh

# 4. Run the setup (replace with your GitHub username and repo)
./setup-ec2.sh petrosrapto PAKTON
```

**At the end, the script will display an SSH private key. COPY IT!** You'll need it in the next step.

### Step 3: Configure GitHub Secrets (10 minutes)

1. **Go to your GitHub repository**
2. **Navigate to**: Settings → Secrets and variables → Actions
3. **Add the following secrets**:

#### EC2 Connection (Copy these from Step 2 output)
```
DEV_EC2_HOST = your-ec2-public-ip
DEV_EC2_USER = ubuntu
DEV_EC2_SSH_KEY = <paste the SSH private key from Step 2>
```

#### Database Credentials (Choose secure values)
```
DEV_POSTGRES_DB = pakton_dev
DEV_POSTGRES_USER = pakton_user
DEV_POSTGRES_PASSWORD = <generate-strong-password>
```

#### Supabase Configuration
```
DEV_SUPABASE_URL = https://your-project.supabase.co
DEV_SUPABASE_JWT_SECRET = <from-supabase-settings>
DEV_ENABLE_AUTHENTICATION = true
```

#### AI/ML Service Keys
```
DEV_OPENAI_API_KEY = sk-...
DEV_HUGGINGFACE_TOKEN = hf_...
DEV_EMBEDDINGS_API_KEY = <your-key>
DEV_TAVILY_API_KEY = tvly-...
DEV_PINECONE_API_KEY = <your-key>
```

#### AWS Credentials
```
DEV_AWS_ACCESS_KEY_ID = AKIA...
DEV_AWS_SECRET_ACCESS_KEY = <your-secret>
DEV_AWS_REGION_NAME = us-west-2
```

#### Frontend Configuration
```
DEV_NEXT_PUBLIC_SUPABASE_URL = https://your-project.supabase.co
DEV_NEXT_PUBLIC_SUPABASE_ANON_KEY = <your-anon-key>
DEV_NEXT_PUBLIC_SUPABASE_URL_DOCUMENTS = https://your-docs-project.supabase.co
DEV_NEXT_PUBLIC_SUPABASE_ANON_KEY_DOCUMENTS = <your-docs-anon-key>
DEV_LOCAL_DEVELOPMENT = true
```

**Optional Secrets** (can be added later):
- `DEV_GOOGLE_API_KEY`
- `DEV_LANGCHAIN_API_KEY`
- `DEV_LANGCHAIN_PROJECT`
- `DEV_NEXT_PUBLIC_GOOGLE_CLIENT_ID`

> 💡 **Tip**: See [deployment/GITHUB_SECRETS.md](deployment/GITHUB_SECRETS.md) for complete reference

### Step 4: Deploy! (2 minutes)

```bash
# On your local machine, commit and push to develop branch
git checkout develop
git add .
git commit -m "Setup CI/CD pipeline"
git push origin develop
```

**That's it!** GitHub Actions will automatically:
1. Build Docker images
2. Push to GitHub Container Registry
3. Deploy to your EC2 instance
4. Run health checks

### Step 5: Verify Deployment (3 minutes)

1. **Watch GitHub Actions**
   - Go to your repo → Actions tab
   - Watch the "Deploy to Dev Environment" workflow

2. **Access Your Application**
   ```
   Frontend: http://YOUR_EC2_IP
   API: http://YOUR_EC2_IP/api
   API Health: http://YOUR_EC2_IP/api/health
   ```

3. **Check Logs** (if needed)
   ```bash
   # SSH into EC2
   ssh -i your-key.pem ubuntu@YOUR_EC2_IP
   
   # View deployment logs
   cat ~/pakton-dev/logs/deployment.log
   
   # Check running containers
   docker ps
   ```

## 🎉 Success!

You now have:
- ✅ Automated CI/CD pipeline
- ✅ Development environment running on EC2
- ✅ All services containerized and orchestrated
- ✅ Nginx reverse proxy configured
- ✅ Automatic deployments on every push to `develop`

## 📚 What's Next?

### Customize Your Deployment
- Update Nginx config: `deployment/nginx/dev.conf`
- Modify deployment script: `deployment/deploy-dev.sh`
- Adjust Docker configurations in the workflow

### Add SSL Certificate
```bash
# SSH into EC2
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Set Up Monitoring
- Configure CloudWatch
- Set up log aggregation
- Enable container metrics

### Production Deployment
- Follow the same pattern for production
- Use `main` branch with release tags
- See `deployment/DEV_SETUP.md` for production guidelines

## 🆘 Troubleshooting

### Deployment Failed?

**Check GitHub Actions logs:**
- Go to Actions tab → Failed workflow → View logs

**Check EC2 logs:**
```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
cat ~/pakton-dev/logs/deployment.log
docker logs pakton-dev-api
docker logs pakton-dev-frontend
```

**Common Issues:**

1. **"Permission denied" during SSH**
   - Verify `DEV_EC2_SSH_KEY` secret is set correctly
   - Check EC2 security group allows SSH from GitHub IPs

2. **"Secret not found"**
   - Verify all required secrets are set in GitHub
   - Check spelling (secrets are case-sensitive)

3. **Containers won't start**
   - Check environment variables are set correctly
   - Verify sufficient EC2 resources (CPU, memory, disk)
   - Check Docker logs: `docker logs <container-name>`

4. **Can't access services**
   - Verify EC2 security group allows HTTP (port 80)
   - Check Nginx: `sudo systemctl status nginx`
   - Verify containers are running: `docker ps`

### Still Having Issues?

1. **Review detailed guides:**
   - [deployment/DEV_SETUP.md](deployment/DEV_SETUP.md) - Complete setup guide
   - [deployment/GITHUB_SECRETS.md](deployment/GITHUB_SECRETS.md) - Secrets reference
   - [deployment/README.md](deployment/README.md) - Deployment architecture

2. **Check individual components:**
   ```bash
   # Check system resources
   htop
   df -h
   
   # Check Docker
   docker ps
   docker stats
   docker system df
   
   # Check Nginx
   sudo nginx -t
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Manual deployment test:**
   ```bash
   cd ~/pakton-dev
   bash deployment/deploy-dev.sh
   ```

## 📞 Support

- **Documentation**: See `deployment/` folder
- **Issues**: Create GitHub issue
- **Contact**: petrosrapto@gmail.com

---

## 🔐 Security Checklist

Before going to production:

- [ ] Change all default passwords
- [ ] Rotate API keys regularly
- [ ] Use separate secrets for dev/prod
- [ ] Enable AWS IAM roles with minimal permissions
- [ ] Install SSL certificate
- [ ] Configure firewall rules
- [ ] Enable security updates
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups
- [ ] Review and restrict security group rules

---

**Estimated Total Setup Time**: 25-30 minutes

**Last Updated**: November 24, 2025
