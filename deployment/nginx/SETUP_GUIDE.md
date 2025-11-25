# PAKTON Nginx, SSL, and DNS Setup Guide

This guide walks you through setting up the complete infrastructure for hosting PAKTON on an EC2 instance with:
- **Production environment** at `pakton.site`
- **Development environment** at `dev.pakton.site`

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [DNS Configuration](#dns-configuration)
3. [EC2 Instance Setup](#ec2-instance-setup)
4. [Nginx Installation and Configuration](#nginx-installation-and-configuration)
5. [SSL Certificates with Let's Encrypt](#ssl-certificates-with-lets-encrypt)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:
- An AWS EC2 instance running Ubuntu/Debian
- SSH access to your EC2 instance
- A registered domain name (e.g., `pakton.site`)
- Access to your domain's DNS provider (e.g., Route 53, Cloudflare, etc.)
- Ports 80 (HTTP) and 443 (HTTPS) open in your EC2 security group

---

## DNS Configuration

### Step 1: Find Your EC2 Public IP

1. Log into AWS Console
2. Navigate to EC2 → Instances
3. Select your instance and copy the **Public IPv4 address** (e.g., `54.123.45.67`)

### Step 2: Configure DNS Records

Log into your DNS provider (Route 53, Cloudflare, etc.) and create the following records:

#### Production Domain (pakton.site)

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ (or pakton.site) | `<YOUR_EC2_IP>` | 300 |
| A | www | `<YOUR_EC2_IP>` | 300 |

**Alternative:** You can use a CNAME for www:
| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | www | pakton.site | 300 |

#### Development Subdomain (dev.pakton.site)

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | dev | `<YOUR_EC2_IP>` | 300 |

**Alternative:** Use CNAME pointing to production:
| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | dev | pakton.site | 300 |

### Step 3: Verify DNS Propagation

Wait a few minutes and verify DNS resolution:

```bash
# Check production domain
dig pakton.site +short
dig www.pakton.site +short

# Check development subdomain
dig dev.pakton.site +short
```

All should return your EC2 IP address.

---

## EC2 Instance Setup

### Step 1: Connect to Your EC2 Instance

```bash
ssh -i /path/to/your-key.pem ubuntu@<YOUR_EC2_IP>
```

### Step 2: Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 3: Configure Security Group

Ensure your EC2 security group allows:

| Type | Protocol | Port Range | Source |
|------|----------|------------|--------|
| HTTP | TCP | 80 | 0.0.0.0/0 |
| HTTPS | TCP | 443 | 0.0.0.0/0 |
| SSH | TCP | 22 | Your IP (recommended) or 0.0.0.0/0 |
| Custom | TCP | 3000 | 127.0.0.1/32 (localhost only) |
| Custom | TCP | 5001 | 127.0.0.1/32 (localhost only) |

**Note:** Ports 3000 and 5001 should only be accessible from localhost since nginx will proxy to them.

---

## Nginx Installation and Configuration

### Step 1: Install Nginx

```bash
sudo apt install nginx -y
```

### Step 2: Start and Enable Nginx

```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```

Verify nginx is running:
```bash
sudo systemctl status nginx
```

### Step 3: Configure Main Nginx Settings

Edit the main nginx configuration:

```bash
sudo nano /etc/nginx/nginx.conf
```

Add rate limiting zones in the `http` block (before the `Virtual Host Configs` section):

```nginx
##
# Rate Limiting Zones
##
limit_req_zone $binary_remote_addr zone=prod_limit:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=dev_limit:10m rate=100r/s;
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

### Step 4: Create Production Site Configuration

Create the production configuration file:

```bash
sudo nano /etc/nginx/sites-available/pakton.site
```

Paste the following configuration:

```nginx
# /etc/nginx/sites-available/pakton.site

# HTTP redirect
server {
    listen 80;
    server_name pakton.site www.pakton.site;
    return 301 https://pakton.site$request_uri;
}

# HTTPS - www redirect
server {
    listen 443 ssl http2;
    server_name www.pakton.site;
    
    ssl_certificate /etc/letsencrypt/live/pakton.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/pakton.site/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    return 301 https://pakton.site$request_uri;
}

# HTTPS - main production
server {
    listen 443 ssl http2;
    server_name pakton.site;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/pakton.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/pakton.site/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logging
    access_log /var/log/nginx/pakton.site.access.log;
    error_log /var/log/nginx/pakton.site.error.log;
    
    # Evaluation service
    location /evaluation/ {
        limit_req zone=prod_limit burst=200 nodelay;
        
        proxy_pass http://localhost:3001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }
    
    # Examples service
    location /examples/ {
        limit_req zone=prod_limit burst=200 nodelay;
        
        proxy_pass http://localhost:8502/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }
    
    # Main service
    location / {
        limit_req zone=prod_limit burst=200 nodelay;
        
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }
}
```

Save and exit.

### Step 5: Create Development Site Configuration

Create the development configuration file:

```bash
sudo nano /etc/nginx/sites-available/dev.pakton.site
```

Paste the following configuration:

```nginx
# /etc/nginx/sites-available/dev.pakton.site

# HTTP redirect
server {
    listen 80;
    server_name dev.pakton.site;
    return 301 https://$server_name$request_uri;
}

# HTTPS - development
server {
    listen 443 ssl http2;
    server_name dev.pakton.site;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/dev.pakton.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dev.pakton.site/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logging
    access_log /var/log/nginx/dev.pakton.site.access.log;
    error_log /var/log/nginx/dev.pakton.site.error.log;
    
    # Dev Frontend (port 3000)
    location / {
        limit_req zone=dev_limit burst=200 nodelay;
        
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 600s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 600s;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "dev-healthy\n";
        add_header Content-Type text/plain;
    }
}
```

Save and exit.

### Step 6: Enable Sites (Without SSL First)

Before getting SSL certificates, we need to enable the sites with temporary HTTP-only configs:

```bash
# Remove SSL-related lines temporarily or skip to SSL section
# For now, we'll enable them after getting certificates
```

---

## SSL Certificates with Let's Encrypt

### Step 1: Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Step 2: Obtain SSL Certificate for Production Domain

Get a certificate for both `pakton.site` and `www.pakton.site`:

```bash
sudo certbot --nginx -d pakton.site -d www.pakton.site
```

You'll be prompted to:
1. Enter your email address (for renewal notifications)
2. Agree to Terms of Service
3. Choose whether to redirect HTTP to HTTPS (select "2" for redirect)

### Step 3: Obtain SSL Certificate for Development Subdomain

```bash
sudo certbot --nginx -d dev.pakton.site
```

Follow the same prompts as above.

### Step 4: Enable Site Configurations

Now enable both sites:

```bash
# Enable production site
sudo ln -s /etc/nginx/sites-available/pakton.site /etc/nginx/sites-enabled/

# Enable development site
sudo ln -s /etc/nginx/sites-available/dev.pakton.site /etc/nginx/sites-enabled/

# Remove default nginx site (optional)
sudo rm /etc/nginx/sites-enabled/default
```

### Step 5: Test Nginx Configuration

```bash
sudo nginx -t
```

You should see:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Step 6: Reload Nginx

```bash
sudo systemctl reload nginx
```

### Step 7: Set Up Automatic Certificate Renewal

Certbot automatically creates a systemd timer for renewal. Verify it:

```bash
sudo systemctl status certbot.timer
```

Test the renewal process:

```bash
sudo certbot renew --dry-run
```

---

## Verification

### Step 1: Check Site Accessibility

#### Production Site
```bash
# Should redirect to HTTPS
curl -I http://pakton.site

# Should return 200 OK
curl -I https://pakton.site
```

Visit in browser: `https://pakton.site`

#### Development Site
```bash
# Should redirect to HTTPS
curl -I http://dev.pakton.site

# Should return 200 OK
curl -I https://dev.pakton.site

# Health check
curl https://dev.pakton.site/health
```

Visit in browser: `https://dev.pakton.site`

### Step 2: Check SSL Certificate

```bash
# Production
echo | openssl s_client -servername pakton.site -connect pakton.site:443 2>/dev/null | openssl x509 -noout -dates

# Development
echo | openssl s_client -servername dev.pakton.site -connect dev.pakton.site:443 2>/dev/null | openssl x509 -noout -dates
```

### Step 3: Verify Application Services

Ensure your applications are running on the correct ports:

**Production (pakton.site):**
- Main service: `localhost:8501`
- Evaluation service: `localhost:3001`
- Examples service: `localhost:8502`

**Development (dev.pakton.site):**
- Frontend: `localhost:3000`
- API: `localhost:5001` (if using API path in future)

Check running services:
```bash
sudo netstat -tlnp | grep -E ':(3000|5001|8501|3001|8502)'
```

---

## Architecture Overview

### Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└──────────────────┬─────────────────┬────────────────────────┘
                   │                 │
                   │                 │
         ┌─────────▼─────────┐  ┌───▼────────────┐
         │   pakton.site     │  │ dev.pakton.site │
         │   (Port 443)      │  │   (Port 443)    │
         └─────────┬─────────┘  └───┬────────────┘
                   │                 │
                   │                 │
         ┌─────────▼─────────────────▼──────────┐
         │         Nginx (Reverse Proxy)        │
         │   - SSL Termination                  │
         │   - Rate Limiting                    │
         │   - Security Headers                 │
         └─────────┬─────────────────┬──────────┘
                   │                 │
                   │                 │
    ┌──────────────▼───────┐    ┌───▼──────────┐
    │  Production Apps     │    │  Dev Apps    │
    │  - Main: 8501        │    │  - Web: 3000 │
    │  - Eval: 3001        │    │  - API: 5001 │
    │  - Examples: 8502    │    │              │
    └──────────────────────┘    └──────────────┘
```

### Key Features

1. **SSL/TLS Encryption**: All traffic encrypted via Let's Encrypt certificates
2. **Automatic HTTP → HTTPS Redirect**: All HTTP requests redirected to HTTPS
3. **Rate Limiting**: 100 requests/second per IP for both environments
4. **Security Headers**: HSTS, X-Frame-Options, etc.
5. **Separate Logging**: Individual access and error logs per environment
6. **WebSocket Support**: Proper headers for real-time connections

---

## Troubleshooting

### Issue: "Connection Refused" or 502 Bad Gateway

**Cause**: Backend services not running on expected ports

**Solution**:
```bash
# Check what's running
sudo netstat -tlnp | grep -E ':(3000|5001|8501)'

# Check Docker containers
docker ps

# Check application logs
docker logs <container-name>
```

### Issue: SSL Certificate Errors

**Cause**: Certificates not properly installed or expired

**Solution**:
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates
sudo certbot renew

# Reload nginx
sudo systemctl reload nginx
```

### Issue: DNS Not Resolving

**Cause**: DNS records not propagated or misconfigured

**Solution**:
```bash
# Check DNS resolution
dig pakton.site +short
dig dev.pakton.site +short

# Check with specific DNS server
dig @8.8.8.8 pakton.site +short
```

Wait up to 24 hours for full DNS propagation (usually much faster).

### Issue: Nginx Configuration Errors

**Cause**: Syntax errors in configuration files

**Solution**:
```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Check site-specific logs
sudo tail -f /var/log/nginx/pakton.site.error.log
sudo tail -f /var/log/nginx/dev.pakton.site.error.log
```

### Issue: Rate Limiting Blocking Legitimate Traffic

**Cause**: Rate limits too restrictive

**Solution**: Adjust the rate in `/etc/nginx/nginx.conf`:
```nginx
# Increase from 100r/s to 200r/s
limit_req_zone $binary_remote_addr zone=prod_limit:10m rate=200r/s;
```

Then reload:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

### Checking Application Health

```bash
# Check nginx status
sudo systemctl status nginx

# Check nginx access logs
sudo tail -f /var/log/nginx/pakton.site.access.log
sudo tail -f /var/log/nginx/dev.pakton.site.access.log

# Check if ports are listening
sudo ss -tlnp | grep -E ':(80|443|3000|5001|8501)'

# Test backend connectivity
curl http://localhost:3000  # Dev frontend
curl http://localhost:8501  # Prod main app
```

---

## Maintenance

### Updating Nginx Configuration

After modifying any nginx configuration:

```bash
# Test configuration
sudo nginx -t

# If test passes, reload
sudo systemctl reload nginx
```

### Monitoring Certificate Expiration

Certificates auto-renew, but you can check:

```bash
# List all certificates and expiration dates
sudo certbot certificates

# Test renewal process
sudo certbot renew --dry-run
```

### Viewing Logs

```bash
# Production logs
sudo tail -f /var/log/nginx/pakton.site.access.log
sudo tail -f /var/log/nginx/pakton.site.error.log

# Development logs
sudo tail -f /var/log/nginx/dev.pakton.site.access.log
sudo tail -f /var/log/nginx/dev.pakton.site.error.log

# Nginx error log
sudo tail -f /var/log/nginx/error.log
```

---

## Security Considerations

1. **Firewall**: Only allow necessary ports (22, 80, 443)
2. **SSH**: Use key-based authentication, disable password login
3. **Updates**: Regularly update system packages and renew certificates
4. **Monitoring**: Set up monitoring for uptime and certificate expiration
5. **Backups**: Backup nginx configs and SSL certificates regularly
6. **Rate Limiting**: Adjust based on your traffic patterns
7. **Security Headers**: Already configured for best practices

---

## Additional Resources

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [AWS EC2 Security Groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html)

---

## Summary

This setup provides:
- ✅ Production environment at `pakton.site` with SSL
- ✅ Development environment at `dev.pakton.site` with SSL
- ✅ Automatic HTTP to HTTPS redirects
- ✅ Rate limiting and security headers
- ✅ Automatic SSL certificate renewal
- ✅ Separate logging per environment
- ✅ WebSocket support for real-time features

Your infrastructure is now ready for the GitHub Actions deployment pipeline!
