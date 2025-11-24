# Adding PAKTON to Your Existing Nginx Setup

This guide shows how to integrate PAKTON services into your existing Nginx configuration on pakton.site.

## Overview

Your current setup serves:
- Main site at `/` (port 8501)
- Evaluation at `/evaluation/` (port 3001)
- Examples at `/examples/` (port 8502)

We'll add:
- **PAKTON API** at `/api/` (Docker container port 5001)
- **PAKTON Frontend** at `/` (ROOT - Docker container port 3000)
- **Old Streamlit Frontend** at `/old/` (moved from root to /old/)
- **Health Check** at `/health`

## Step 1: Deploy Docker Containers

First, deploy the PAKTON containers (they'll run on localhost ports):

```bash
cd ~/pakton-dev
bash deployment/deploy-dev.sh
```

This will start:
- API on `localhost:5001`
- Frontend on `localhost:3000`
- RabbitMQ Management on `localhost:15672`

## Step 2: Add Upstream Definitions

Edit your Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/streamlit
```

**Add these upstream definitions at the TOP of the file** (before the first `server` block):

```nginx
# PAKTON Upstream Definitions
upstream pakton_api {
    server localhost:5001;
}

upstream pakton_frontend {
    server localhost:3000;
}

upstream pakton_rabbitmq {
    server localhost:15672;
}
```

## Step 3: Add PAKTON Location Blocks

In the **HTTPS server block** (the one with SSL certificates), **replace the existing locations** with these new ones in this order:

Find this line:
```nginx
server {
    server_name pakton.site www.pakton.site;
```

After it, add the PAKTON locations, then your existing /evaluation/ and /examples/, and finally move the root / to /old/:

```nginx
    # ============================================
    # PAKTON Services
    # ============================================
    
    # PAKTON API - accessible at https://pakton.site/api/
    location /api/ {
        # Remove /api prefix before proxying to backend
        rewrite ^/api/(.*) /$1 break;
        
        proxy_pass http://pakton_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE/Streaming support (important for long-running queries)
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Evaluation app (keep as is)
    location /evaluation/ {
        proxy_pass http://localhost:3001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Examples app (keep as is)
    location /examples/ {
        proxy_pass http://localhost:8502/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Old PAKTON Frontend (previously at root) - now at /old/
    location /old/ {
        proxy_pass http://localhost:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # New PAKTON Frontend - NOW AT ROOT
    location / {
        proxy_pass http://pakton_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }

    # ============================================
    # End PAKTON Services
    # ============================================
```

## Step 4: Optional - Add RabbitMQ Management UI (Dev Only)

If you want to access RabbitMQ management interface, add:

```nginx
    # RabbitMQ Management UI (Development only - remove in production)
    location /rabbitmq/ {
        # Optional: Add basic auth for security
        # auth_basic "Restricted Access";
        # auth_basic_user_file /etc/nginx/.htpasswd;
        
        rewrite ^/rabbitmq/(.*) /$1 break;
        proxy_pass http://pakton_rabbitmq;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
```

## Step 5: Optional - Add Rate Limiting

For production, add rate limiting to the `http` block in `/etc/nginx/nginx.conf`:

```bash
sudo nano /etc/nginx/nginx.conf
```

Find the `http {` block and add near the top:

```nginx
http {
    # ... existing settings ...
    
    # PAKTON Rate limiting zones
    limit_req_zone $binary_remote_addr zone=pakton_api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=pakton_frontend_limit:10m rate=30r/s;
    
    # ... rest of http block ...
}
```

Then in your location blocks, add:

```nginx
    location /api/ {
        limit_req zone=pakton_api_limit burst=20 nodelay;
        # ... rest of configuration ...
    }

    location /pakton/ {
        limit_req zone=pakton_frontend_limit burst=50 nodelay;
        # ... rest of configuration ...
    }
```

## Step 6: Test and Reload Nginx

Test the configuration:

```bash
sudo nginx -t
```

If successful, reload Nginx:

```bash
sudo systemctl reload nginx
```

## Step 7: Verify

Test your endpoints:

```bash
# Health check
curl https://pakton.site/health

# API health (if you have a /health endpoint in your API)
curl https://pakton.site/api/health

# New PAKTON Frontend (at root)
curl https://pakton.site/

# Old Streamlit Frontend
curl https://pakton.site/old/

# Full API test with authentication
curl -X POST https://pakton.site/api/query/sse \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "Hello"}'
```

## Complete Example Configuration

Your final `/etc/nginx/sites-available/streamlit` should look like:

```nginx
# PAKTON Upstream Definitions
upstream pakton_api {
    server localhost:5001;
}

upstream pakton_frontend {
    server localhost:3000;
}

upstream pakton_rabbitmq {
    server localhost:15672;
}

server {
    server_name pakton.site www.pakton.site;

    # PAKTON API
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        
        proxy_pass http://pakton_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
        
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
        
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }

    # PAKTON Frontend
    location /pakton/ {
        proxy_pass http://pakton_frontend/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Your existing locations
    location /evaluation/ {
        proxy_pass http://localhost:3001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /examples/ {
        proxy_pass http://localhost:8502/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Old Streamlit Frontend - moved from root to /old/
    location /old/ {
        proxy_pass http://localhost:8501/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # New PAKTON Frontend - NOW AT ROOT
    location / {
        proxy_pass http://pakton_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/pakton.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/pakton.site/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = www.pakton.site) {
        return 301 https://$host$request_uri;
    }

    if ($host = pakton.site) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    server_name pakton.site www.pakton.site;
    return 404;
}
```

## Troubleshooting

### API returns 502 Bad Gateway
```bash
# Check if API container is running
docker ps | grep pakton-dev-api

# Check API logs
docker logs pakton-dev-api

# Test API directly
curl http://localhost:5001/health
```

### Frontend returns 502 Bad Gateway
```bash
# Check if Frontend container is running
docker ps | grep pakton-dev-frontend

# Check Frontend logs
docker logs pakton-dev-frontend

# Test Frontend directly
curl http://localhost:3000
```

### Nginx errors
```bash
# Check Nginx error log
sudo tail -f /var/log/nginx/error.log

# Test configuration
sudo nginx -t

# Restart Nginx if needed
sudo systemctl restart nginx
```

### CORS errors in browser
- Make sure the CORS headers are in the correct location block
- Check that the `if ($request_method = 'OPTIONS')` block is present
- Verify headers with browser DevTools Network tab

## URLs After Setup

Once configured, your services will be available at:

- **Main Site**: https://pakton.site
- **Evaluation**: https://pakton.site/evaluation/
- **Examples**: https://pakton.site/examples/
- **PAKTON API**: https://pakton.site/api/
- **PAKTON Frontend**: https://pakton.site/pakton/
- **Health Check**: https://pakton.site/health
- **RabbitMQ** (if enabled): https://pakton.site/rabbitmq/

## Security Notes

1. **Rate Limiting**: Recommended for production to prevent abuse
2. **RabbitMQ**: Should be removed or protected with basic auth in production
3. **CORS**: Currently set to `*` - restrict to your frontend domain in production
4. **SSL**: Already configured with Let's Encrypt ✅
5. **Firewall**: Ensure only ports 22, 80, 443 are exposed on EC2

## Next Steps

1. Update your frontend code to use `https://pakton.site/api/` as the API base URL
2. Test all endpoints thoroughly
3. Monitor Nginx and Docker logs during initial deployment
4. Set up monitoring/alerting for the new services
5. Configure automated backups for the PostgreSQL database

---

**Need Help?**
- Check logs: `sudo tail -f /var/log/nginx/error.log`
- Docker logs: `docker logs pakton-dev-api`
- Test config: `sudo nginx -t`
