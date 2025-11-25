# PAKTON Nginx Configuration

This directory contains nginx configuration files for PAKTON's production and development environments.

## Files

- **`SETUP_GUIDE.md`** - Complete setup guide for nginx, SSL certificates, and DNS
- **`nginx.conf`** - Main nginx configuration with rate limiting zones
- **`pakton.site`** - Production site configuration
- **`dev.pakton.site`** - Development site configuration

## Quick Reference

### Production Setup
- **Domain**: `pakton.site`
- **Services**: Main (8501), Evaluation (3001), Examples (8502)
- **SSL**: Let's Encrypt certificates

### Development Setup
- **Domain**: `dev.pakton.site`
- **Services**: Frontend (3000), API (5001 - future)
- **SSL**: Let's Encrypt certificates

## Setup Instructions

For complete setup instructions including DNS configuration, nginx installation, and SSL certificates, see:

**[SETUP_GUIDE.md](SETUP_GUIDE.md)**

## Quick Commands

```bash
# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check SSL certificates
sudo certbot certificates

# View logs
sudo tail -f /var/log/nginx/pakton.site.error.log
sudo tail -f /var/log/nginx/dev.pakton.site.error.log
```

---

**For detailed setup**: See [SETUP_GUIDE.md](SETUP_GUIDE.md)
