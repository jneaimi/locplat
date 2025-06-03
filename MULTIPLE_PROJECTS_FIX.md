# Coolify Multiple Projects Port Conflict Resolution

## Issue: Two Projects on Same Server
- ✅ Working project: Uses port 8000 (directus-translator)
- ❌ New project: LocPlat (trying to use port 8000)

## Solutions:

### Option 1: Change LocPlat Internal Port (Recommended)
Change your FastAPI app to run on port 8080 internally:

1. **Update Dockerfile CMD:**
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

2. **Update SERVICE_FQDN:**
```yaml
environment:
  - SERVICE_FQDN_API_8080=locplat.estatfinder.com
```

### Option 2: Copy Working Project Configuration
Can you share your working directus-translator docker-compose file? I need to see:
- How it configures domains
- What environment variables it uses
- How it handles Coolify integration

### Option 3: Use Different Service Name
Change service name from 'api' to 'locplat':
```yaml
services:
  locplat:  # Instead of 'api'
    environment:
      - SERVICE_FQDN_LOCPLAT_8000=locplat.estatfinder.com
```

## Quick Test Commands:
```bash
# Check what's using port 8000
docker ps | grep :8000

# See your working project configuration
docker inspect <working-container-name> | grep -A 10 -B 5 Labels
```

## Questions:
1. Can you share the docker-compose.yml from your working directus-translator project?
2. How is the domain configured in that project?
3. Does it use SERVICE_FQDN or different labels?

The key is to see what makes your other project work on Coolify!