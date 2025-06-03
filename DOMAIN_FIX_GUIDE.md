# Coolify Domain Configuration Fix

## Issue: Domain Not Working, Server IP Works ✅

Your API is accessible via server IP:8090 but not through your domain.

## Root Cause Analysis:

Looking at your docker ps, I see you have `coolify-proxy` running:
```
coolify-proxy   0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

This means Coolify's reverse proxy is active, but your LocPlat service isn't configured to use it.

## Solutions:

### Option 1: Configure Domain in Coolify (Recommended)

1. **In Coolify Dashboard:**
   - Go to your LocPlat service
   - Find "Domains" or "URLs" section
   - Add your domain: `yourdomain.com` or `api.yourdomain.com`
   - Enable HTTPS/SSL if needed

2. **Coolify will automatically:**
   - Configure reverse proxy
   - Handle SSL certificates
   - Route domain traffic to port 8090

### Option 2: Manual Proxy Configuration

If Coolify doesn't handle it automatically, you need to configure the reverse proxy.

#### Check Current Proxy Configuration:
```bash
# Check if Caddy is handling your domain
docker exec coolify-proxy caddy list-configs

# Check proxy logs
docker logs coolify-proxy
```

### Option 3: Service-Level Domain Configuration

In your Coolify service:

1. **Environment Variables to add:**
   ```env
   VIRTUAL_HOST=yourdomain.com
   VIRTUAL_PORT=8000
   LETSENCRYPT_HOST=yourdomain.com
   LETSENCRYPT_EMAIL=your-email@domain.com
   ```

2. **Or configure in docker-compose.coolify.yml:**
   ```yaml
   api:
     labels:
       - "caddy=yourdomain.com"
       - "caddy.reverse_proxy={{upstreams 8000}}"
   ```

### Troubleshooting Steps:

1. **Check DNS:**
   ```bash
   nslookup yourdomain.com
   dig yourdomain.com
   ```

2. **Test domain connectivity:**
   ```bash
   curl -v http://yourdomain.com
   curl -v https://yourdomain.com
   ```

3. **Check if domain reaches server:**
   ```bash
   # On your server
   tail -f /var/log/nginx/access.log  # if using nginx
   # or check Coolify proxy logs
   docker logs -f coolify-proxy
   ```

### Expected Result:
- `http://yourdomain.com` → redirects to your LocPlat API
- `https://yourdomain.com/docs` → API documentation
- `https://yourdomain.com/health` → health check

## Quick Test:
1. Add domain in Coolify dashboard first
2. Wait 2-3 minutes for configuration
3. Test: `curl http://yourdomain.com/health`

The issue is likely that Coolify's reverse proxy isn't configured to route your domain to the LocPlat service on port 8090.