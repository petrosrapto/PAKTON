# PAKTON Multi-Environment Nginx Setup Guide

This guide explains how to set up both **development** and **production** environments for PAKTON on the same EC2 instance.

## 📋 Overview

| Environment | Domain | Ports | Auto-Deploy |
|------------|--------|-------|-------------|
| **Production** | `pakton.site` | API: 5001, Frontend: 3000 | ❌ Manual (release tags) |
| **Development** | `dev.pakton.site` | API: 5002, Frontend: 3001 | ✅ Auto (develop branch) |

## 🏗️ Architecture

```
EC2 Instance (Nginx Host)
├── Production (pakton.site)
│   ├── / → Frontend (port 3000)
│   ├── /api/ → API (port 5001)
│   └── /old/ → Old Streamlit (port 8501)
│
├── Development (dev.pakton.site)
│   ├── / → Frontend (port 3001)
│   ├── /api/ → API (port 5002)
│   └── /rabbitmq/ → RabbitMQ UI (port 15672)
│
└── Existing Services
    ├── /evaluation/ → port 3002
    └── /examples/ → port 8502
```

## 🚀 Setup Steps

### Step 1: DNS Configuration

Add an A record for the dev subdomain:

```
Type: A
Host: dev
Value: <Your EC2 IP Address>
TTL: Auto
```

Verify DNS propagation:
```bash
dig dev.pakton.site
```

### Step 2: Update Deployment Scripts

The deployment scripts need to use different ports for dev vs production:

**For Development (`deploy-dev.sh`)**:
- API: port 5002
- Frontend: port 3001
- RabbitMQ Management: port 15672

**For Production (`deploy-prod.sh`)** (to be created):
- API: port 5001
- Frontend: port 3000
- RabbitMQ Management: disabled

### Step 3: Configure Nginx for Development

1. Create the dev site configuration:
```bash
sudo nano /etc/nginx/sites-available/dev.pakton.site
```

2. Copy the entire server block from `deployment/nginx/dev.conf`

3. Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/dev.pakton.site /etc/nginx/sites-enabled/
```

4. Test configuration:
```bash
sudo nginx -t
```

5. Get SSL certificate for dev subdomain:
```bash
sudo certbot --nginx -d dev.pakton.site
```

6. Reload Nginx:
```bash
sudo systemctl reload nginx
```

### Step 4: Configure Nginx for Production

1. Edit your existing production site config:
```bash
sudo nano /etc/nginx/sites-available/pakton.site
```

2. Add the upstream definitions and location blocks from `deployment/nginx/production.conf`

3. Test and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5: Update docker-compose Port Mappings

You need to ensure containers expose different ports for dev vs production.

**Development** (`docker-compose.dev.yml`):
```yaml
services:
  api:
    ports:
      - "5002:8000"  # Changed from 5001
  frontend:
    ports:
      - "3001:3000"  # Changed from 3000
    environment:
      - NEXT_PUBLIC_API_URL=https://dev.pakton.site/api
  rabbitmq:
    ports:
      - "15672:15672"
```

**Production** (`docker-compose.prod.yml`):
```yaml
services:
  api:
    ports:
      - "5001:8000"
  frontend:
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://pakton.site/api
  # No RabbitMQ management UI exposed
```

## 📝 Configuration Files Summary

| File | Purpose | Use Case |
|------|---------|----------|
| `nginx.conf` | Original snippets (deprecated) | ⚠️ Replace with production.conf |
| `production.conf` | Production environment config | Add to pakton.site server block |
| `dev.conf` | Development environment config | Create new dev.pakton.site server block |

**Recommendation**: 
- Delete `nginx.conf` after migrating to `production.conf` and `dev.conf`
- Keep `production.conf` and `dev.conf` as reference documentation

## 🔐 Security Considerations

### Production (`pakton.site`)
- ✅ Strict rate limiting (10 req/s API, 30 req/s frontend)
- ✅ CORS restricted to `https://pakton.site`
- ✅ No RabbitMQ management UI exposed
- ✅ Production-grade timeouts

### Development (`dev.pakton.site`)
- ⚠️ Relaxed rate limiting (30 req/s API, 100 req/s frontend)
- ⚠️ CORS allows all origins (`*`)
- ⚠️ RabbitMQ management UI accessible
- ⚠️ Longer timeouts for debugging

## 🧪 Testing

### Development Environment
```bash
# Health check
curl https://dev.pakton.site/health

# API test
curl https://dev.pakton.site/api/health

# Frontend (browser)
open https://dev.pakton.site

# RabbitMQ UI (browser)
open https://dev.pakton.site/rabbitmq/
```

### Production Environment
```bash
# Health check
curl https://pakton.site/health

# API test
curl https://pakton.site/api/health

# Frontend (browser)
open https://pakton.site

# Old Streamlit (browser)
open https://pakton.site/old/
```

## 📊 Monitoring

Check which services are running on which ports:
```bash
# On EC2
sudo netstat -tlnp | grep -E ':(3000|3001|5001|5002|8501|15672)'
```

Expected output:
```
tcp6  0  0 :::3000  :::*  LISTEN  <pid>/docker-proxy  # Production Frontend
tcp6  0  0 :::3001  :::*  LISTEN  <pid>/docker-proxy  # Dev Frontend
tcp6  0  0 :::5001  :::*  LISTEN  <pid>/docker-proxy  # Production API
tcp6  0  0 :::5002  :::*  LISTEN  <pid>/docker-proxy  # Dev API
tcp6  0  0 :::8501  :::*  LISTEN  <pid>/streamlit     # Old Frontend
tcp6  0  0 :::15672 :::*  LISTEN  <pid>/docker-proxy  # Dev RabbitMQ
```

## 🔄 Deployment Workflow

### Development (Automatic)
1. Push to `develop` branch
2. GitHub Actions builds & deploys to dev environment
3. Services available at `dev.pakton.site`

### Production (Manual)
1. Merge to `main` branch (triggers build/test)
2. Create release tag (`v1.0.0`)
3. GitHub Actions builds & deploys to production
4. Services available at `pakton.site`

## 🐛 Troubleshooting

### Port Conflicts
If you get "address already in use" errors:
```bash
# Find what's using the port
sudo lsof -i :5001
sudo lsof -i :3000

# Stop conflicting services
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.prod.yml down
```

### SSL Certificate Issues
```bash
# Check certificates
sudo certbot certificates

# Renew if needed
sudo certbot renew --dry-run
```

### Nginx Configuration Errors
```bash
# Test configuration
sudo nginx -t

# View error logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/dev.pakton.site.error.log
```

### CORS Issues
If frontend can't reach API:
1. Check `NEXT_PUBLIC_API_URL` in frontend container
2. Verify CORS headers in Nginx config
3. Check browser console for CORS errors

## 📚 Next Steps

1. **Update `deploy-dev.sh`** - Change ports to 5002 (API) and 3001 (Frontend)
2. **Create `deploy-prod.sh`** - Use ports 5001 (API) and 3000 (Frontend)
3. **Create production workflow** - `.github/workflows/deploy-prod.yml`
4. **Test development deployment** - Push to develop branch
5. **Migrate production config** - Add snippets from `production.conf` to existing site

---

**Questions?** Check the main deployment documentation in `deployment/README.md`
