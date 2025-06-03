# Coolify Domain Debugging Checklist

## Current Status:
- ✅ Caddy labels added to docker-compose.coolify.yml
- ✅ Code committed to GitHub
- ❌ Domain still not working

## Debug Steps:

### 1. Check Coolify Service Configuration
In your Coolify dashboard:
- **Verify docker-compose file**: Make sure it's using `docker-compose.coolify.yml`
- **Check environment variables**: Ensure `DOMAIN_NAME=locplat.estatfinder.com` is set
- **Domain configuration**: Look for a "Domains" or "URLs" section and add your domain there

### 2. Check Container Logs
Run these commands on your server:

```bash
# Check if the API container is running
docker ps | grep api

# Check API container logs
docker logs <api-container-name>

# Check Coolify proxy logs
docker logs coolify-proxy | grep locplat

# Check if domain is registered in Caddy
docker exec coolify-proxy caddy list-configs | grep locplat
```

### 3. Test Container Network
```bash
# Check if containers are in the same network
docker network ls | grep coolify
docker network inspect coolify | grep -A 5 -B 5 api
```

### 4. Check SSL Certificate Generation
```bash
# Check if SSL cert was generated
docker exec coolify-proxy ls -la /data/caddy/certificates/ | grep estatfinder

# Test SSL certificate
echo | openssl s_client -connect locplat.estatfinder.com:443 -servername locplat.estatfinder.com
```

### 5. Manual Domain Test
```bash
# Test if domain reaches your server at all
curl -v https://locplat.estatfinder.com/
curl -v http://locplat.estatfinder.com/

# Test direct server access (should work)
curl http://YOUR_SERVER_IP:8090/health
```

## Common Issues:

### Issue 1: Domain Not Added in Coolify UI
- **Solution**: Go to service → Domains → Add `locplat.estatfinder.com`

### Issue 2: Wrong Docker Compose File
- **Solution**: Ensure Coolify is using `docker-compose.coolify.yml` (not docker-compose.yml)

### Issue 3: Network Problems
- **Solution**: Add network configuration to docker-compose

### Issue 4: Environment Variable Not Set
- **Solution**: Add `DOMAIN_NAME=locplat.estatfinder.com` in Coolify environment variables

## Next Steps:
1. Run the debug commands above
2. Share the output of container logs
3. Check Coolify UI domain configuration
4. Verify which docker-compose file is being used