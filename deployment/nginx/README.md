# Nginx Configuration Files - Quick Reference

## 📁 Files Overview

| File | Purpose | When to Use |
|------|---------|-------------|
| **`production.conf`** | Production environment (pakton.site) | Add snippets to existing pakton.site server block |
| **`dev.conf`** | Development environment (dev.pakton.site) | Create new server block for dev subdomain |
| **`nginx.conf`** | ❌ **DEPRECATED** - Original mixed snippets | Delete after migration |
| **`ENVIRONMENTS_GUIDE.md`** | Complete setup guide | Read first for full setup instructions |
| **`INTEGRATION_GUIDE.md`** | Original integration guide | Reference for basic Nginx concepts |

## ✅ What You Should Keep

**Keep these 3 files:**
1. **`production.conf`** - Production configuration snippets
2. **`dev.conf`** - Development configuration (complete server block)
3. **`ENVIRONMENTS_GUIDE.md`** - Setup instructions

**Delete this file:**
- **`nginx.conf`** - This was the original combined configuration before we separated dev and production

## 🎯 Quick Decision Guide

**Q: I want to set up dev.pakton.site**
- Use: `dev.conf` 
- Action: Copy entire server blocks to `/etc/nginx/sites-available/dev.pakton.site`

**Q: I want to add PAKTON to pakton.site**
- Use: `production.conf`
- Action: Add upstream definitions and location blocks to existing `/etc/nginx/sites-available/pakton.site`

**Q: I need step-by-step instructions**
- Read: `ENVIRONMENTS_GUIDE.md`

## 🔧 Port Assignments

### Production (pakton.site)
- API: `5001`
- Frontend: `3000`
- RabbitMQ: Not exposed

### Development (dev.pakton.site)
- API: `5002` ⚠️ **You need to update deploy-dev.sh**
- Frontend: `3001` ⚠️ **You need to update deploy-dev.sh**
- RabbitMQ UI: `15672`

## ⚠️ Important Notes

1. **Port Conflicts**: Dev and production use DIFFERENT ports to run simultaneously
2. **DNS Required**: You need to add `dev.pakton.site` A record pointing to your EC2 IP
3. **SSL Certificates**: Run `sudo certbot --nginx -d dev.pakton.site` after Nginx setup
4. **Deployment Scripts**: Update `deploy-dev.sh` to use ports 5002 and 3001 (not 5001 and 3000)

## 🚀 Next Steps

1. **Delete the old file**: 
   ```bash
   rm deployment/nginx/nginx.conf
   ```

2. **Read the complete guide**:
   ```bash
   cat deployment/nginx/ENVIRONMENTS_GUIDE.md
   ```

3. **Update deployment script** to use dev ports (5002, 3001)

4. **Set up DNS** for dev.pakton.site

5. **Deploy both environments** following the guide

---

**Questions?** See `ENVIRONMENTS_GUIDE.md` for complete instructions.
