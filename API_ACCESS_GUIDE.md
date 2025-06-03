# LocPlat API Testing Commands

## Your LocPlat API is running on PORT 8090! 🎉

### Test Commands (replace YOUR_SERVER_IP):

```bash
# Health Check
curl http://YOUR_SERVER_IP:8090/health

# API Documentation (in browser)
http://YOUR_SERVER_IP:8090/docs

# Root endpoint
curl http://YOUR_SERVER_IP:8090/

# API Info
curl http://YOUR_SERVER_IP:8090/api/v1/info

# Translation providers
curl http://YOUR_SERVER_IP:8090/api/v1/translate/providers

# Cache status
curl http://YOUR_SERVER_IP:8090/api/v1/cache/info
```

### Container Status ✅
- API Container: `api-eoc084sskc8cowswosssg4c8-080552211726` (HEALTHY)
- Port Mapping: `0.0.0.0:8090->8000/tcp`
- PostgreSQL: HEALTHY 
- Redis: HEALTHY

### Next Steps:
1. Test the health endpoint first
2. Open API docs in browser
3. Configure domain/proxy in Coolify if needed
4. Test translation functionality

Your deployment is successful! 🚀