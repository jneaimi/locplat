# Coolify Deployment Troubleshooting

## Current Issue Analysis

Based on your error logs, the deployment failed because:

1. **Missing Environment Variables**:
   - `API_PORT` - not set, defaulting to blank
   - `REDIS_PASSWORD` - not set, defaulting to blank

2. **Container Health Check Failures**:
   - Redis container unhealthy (authentication failing)
   - PostgreSQL container unhealthy (connection issues)
   - API container dependency failure

## Immediate Fix Steps

### Step 1: Set Environment Variables in Coolify

In your Coolify service settings, add these environment variables:

```env
API_PORT=8000
REDIS_PASSWORD=Redis2025Secure#LocPlat$Cache!
POSTGRES_PASSWORD=PgSql2025Secure#LocPlat$Database!
SECRET_KEY=8f9a2b7d4e6c3a1f9e8b7c5d2a4f6e9b1c8d5f2a7e4b9c6d3f1a8e5b2c9f6d3a
WEBHOOK_SECRET=3c6f9e2b5d8a1f4e7b9c2d5a8f1e4b7c9d6f3a1e8b5c2f9d6a3e1f8c5b2d9a6f
POSTGRES_USER=locplat_user
POSTGRES_DB=locplat_production
ENVIRONMENT=production
```

### Step 2: Verify Docker Compose File

Ensure Coolify is using `docker-compose.prod.yml` (not `docker-compose.yml`)

### Step 3: Check Health Dependencies

The production compose file has health check dependencies that may be too strict for initial deployment.

## Quick Test Commands

```bash
# Test if containers start individually
docker-compose -f docker-compose.prod.yml up postgres redis

# Check container logs
docker-compose -f docker-compose.prod.yml logs redis
docker-compose -f docker-compose.prod.yml logs postgres
```

## Alternative: Simplified Deployment

If health checks continue to fail, use this simplified version temporarily.