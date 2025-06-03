# Cloudflare + Coolify Configuration Fix

## Issue: HTTP 525 Error - SSL Handshake Failed

Your domain `locplat.estatfinder.com` is behind Cloudflare, but there's an SSL mismatch.

## Root Cause:
- Cloudflare expects HTTPS connection to your origin server
- Your Coolify service serves HTTP on port 8090
- Mismatch causes HTTP 525 error

## Solution 1: Fix Cloudflare SSL Settings (IMMEDIATE FIX)

### In Cloudflare Dashboard:

1. **Go to SSL/TLS tab**
2. **Change SSL/TLS encryption mode to: "Flexible"**
   - This allows Cloudflare to connect to your origin via HTTP
   - Visitors still get HTTPS from Cloudflare

3. **Alternative: Use "Full" mode with these settings:**
   - SSL/TLS: Full (not "Full (strict)")
   - This works with self-signed certs

### DNS Configuration:
Make sure your DNS A record points to your actual server IP, not Cloudflare proxy:
```
Type: A
Name: locplat
Value: YOUR_ACTUAL_SERVER_IP
Proxy: Orange cloud (ON) - keep this for Cloudflare protection
```

## Solution 2: Update Coolify for HTTPS (ADVANCED)

If you want proper end-to-end encryption:

1. **In Coolify, enable SSL for your domain**
2. **Add environment variable:**
   ```env
   DOMAIN_NAME=locplat.estatfinder.com
   ```
3. **Redeploy service**
4. **Set Cloudflare to "Full (strict)" SSL mode**

## Solution 3: Bypass Cloudflare Temporarily

To test if the service works:
1. **Set DNS record to "DNS only" (gray cloud)**
2. **Test: `curl http://YOUR_SERVER_IP:8090/health`**
3. **Re-enable proxy after Coolify SSL is configured**

## Quick Test After Fix:
```bash
curl https://locplat.estatfinder.com/health
curl https://locplat.estatfinder.com/docs
```

## Expected Result:
- ✅ HTTPS works through Cloudflare
- ✅ API accessible via domain
- ✅ SSL certificate valid
- ✅ Server remains protected by Cloudflare

**RECOMMENDATION: Start with Solution 1 (Flexible SSL) for immediate fix.**