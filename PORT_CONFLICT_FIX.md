# Coolify Port Conflict Resolution

## Issue: Port 8000 Already Allocated

### Quick Fixes:

#### Option 1: Change Port (Recommended)
Update your Coolify environment variables:
```env
API_PORT=8080
```

#### Option 2: Use Dynamic Port
In Coolify, let it auto-assign the port:
```env
# Remove API_PORT or set to empty
API_PORT=
```

#### Option 3: Clean Previous Deployment
In Coolify dashboard:
1. Stop all running services
2. Clean up containers: `docker container prune -f`
3. Redeploy

### New Environment Variable Issues:

The logs show missing "Database" and "Cache" variables. These might be from variable interpolation in docker-compose.

#### Fix Environment Variables:
Add these to Coolify:
```env
Database=locplat_production
Cache=redis_cache
POSTGRES_DB=locplat_production
REDIS_DB=0
```

### Troubleshooting Commands:

```bash
# Check what's using port 8000
sudo lsof -i :8000
sudo netstat -tulpn | grep :8000

# Stop conflicting services
docker ps | grep :8000
docker stop <container_id>

# Clean up Docker
docker container prune -f
docker network prune -f
```

### Recommended Solution:

1. **Change API_PORT to 8080** in Coolify environment variables
2. **Add missing Database/Cache variables**
3. **Redeploy the service**

The port conflict is a common issue in shared hosting environments like Coolify.