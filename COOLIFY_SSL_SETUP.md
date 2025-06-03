# Enable SSL/HTTPS on Coolify Server - Keep Cloudflare Full SSL

## Goal: Make your server support HTTPS so Cloudflare can connect securely

## Solution 1: Configure Coolify Domain with SSL (Recommended)

### Step 1: Add Domain in Coolify Dashboard
1. **Go to your LocPlat service in Coolify**
2. **Find "Domains" section**
3. **Add domain: `locplat.estatfinder.com`**
4. **Enable "Generate SSL Certificate" (Let's Encrypt)**
5. **Save configuration**

### Step 2: Update Environment Variables
Add these in Coolify:
```env
DOMAIN_NAME=locplat.estatfinder.com
VIRTUAL_HOST=locplat.estatfinder.com
VIRTUAL_PORT=8000
LETSENCRYPT_HOST=locplat.estatfinder.com
LETSENCRYPT_EMAIL=your-email@domain.com
```

### Step 3: Verify Coolify Proxy Configuration
Coolify should automatically:
- Generate SSL certificate via Let's Encrypt
- Configure reverse proxy (Caddy)
- Route `locplat.estatfinder.com` → your service on port 8090

## Solution 2: Manual SSL Configuration with Docker Labels

Update docker-compose.coolify.yml with SSL labels: