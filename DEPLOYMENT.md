# 🚀 LocPlat Production Deployment Guide

## Overview
This guide covers deploying LocPlat to production using Coolify cloud platform with proper security, monitoring, and performance optimization.

## Prerequisites

### Required Accounts & Access
- Coolify account with server access
- Domain name configured for your deployment
- SSL certificate management (Coolify handles this automatically)

### Security Requirements
- Strong passwords (minimum 16 characters)
- Unique secret keys (32+ character random strings)
- Proper CORS origins configuration

## 📋 Pre-Deployment Checklist

### 1. Environment Configuration
- [ ] Copy `.env.production.template` to `.env.production`
- [ ] Replace all placeholder values with secure credentials
- [ ] Configure proper domain names in CORS_ORIGINS
- [ ] Generate secure SECRET_KEY and WEBHOOK_SECRET

### 2. Security Validation
- [ ] Ensure `.env.production` is in `.gitignore`
- [ ] Verify no hardcoded credentials in code
- [ ] Review ALLOWED_HOSTS configuration
- [ ] Confirm database authentication method (scram-sha-256)

### 3. Resource Planning
- [ ] Review CPU and memory limits based on expected load
- [ ] Plan for database backup strategy
- [ ] Configure monitoring and alerting

## 🔧 Deployment Steps

### Step 1: Prepare Production Environment

```bash
# 1. Create production environment file
cp .env.production.template .env.production

# 2. Generate secure secrets (use these commands or similar)
# For SECRET_KEY and WEBHOOK_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Edit .env.production with your values
nano .env.production
```

**Required Changes in .env.production:**
- `SECRET_KEY`: 32+ character random string
- `WEBHOOK_SECRET`: 32+ character random string  
- `POSTGRES_PASSWORD`: Strong database password
- `REDIS_PASSWORD`: Strong Redis password
- `ALLOWED_HOSTS`: Your domain(s)
- `CORS_ORIGINS`: Your frontend URLs

### Step 2: Validate Configuration

```bash
# Test production docker-compose syntax
docker-compose -f docker-compose.prod.yml config

# Verify environment variables are loaded
docker-compose -f docker-compose.prod.yml --env-file .env.production config
```

### Step 3: Coolify Deployment

1. **Create New Service in Coolify**
   - Go to your Coolify dashboard
   - Click "Create new resource" → "Docker Compose"
   - Connect to your Git repository

2. **Configure Build Settings**
   - Docker Compose file: `docker-compose.prod.yml`
   - Environment: Upload your `.env.production` file
   - Build context: Root directory

3. **Set Environment Variables**
   Copy all variables from `.env.production` to Coolify's environment section

4. **Configure Domains**
   - Add your domain name
   - Enable automatic HTTPS/SSL
   - Configure any subdomain redirects

### Step 4: Database Initialization

The PostgreSQL container will automatically:
- Create the database with proper authentication
- Run any SQL scripts in `/scripts/init-db.sql`
- Set up user permissions

### Step 5: Post-Deployment Verification

```bash
# 1. Check health endpoints
curl https://yourdomain.com/health

# 2. Verify API functionality
curl https://yourdomain.com/api/v1/status

# 3. Test translation endpoint
curl -X POST https://yourdomain.com/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello","target_language":"ar","api_key":"your-openai-key"}'
```

## 🔒 Security Considerations

### Environment Variables Security
- Never commit `.env.production` to version control
- Use Coolify's encrypted environment variable storage
- Rotate secrets regularly (quarterly recommended)

### Database Security  
- Use strong passwords (16+ characters with mixed case, numbers, symbols)
- Enable scram-sha-256 authentication
- Regular backups with encryption

### Network Security
- HTTPS only (Coolify handles SSL automatically)
- Proper CORS configuration
- Rate limiting enabled

### Application Security
- Client-provided API keys (no storage)
- Input validation and sanitization
- Structured logging for audit trails

## 📊 Monitoring & Maintenance

### Health Checks
The deployment includes comprehensive health checks:
- API health endpoint: `/health`
- Database connectivity validation
- Redis cache verification

### Resource Monitoring
Monitor these metrics in Coolify:
- CPU usage (should stay under 80%)
- Memory usage (watch for memory leaks)
- Response times
- Error rates

### Log Management
- Application logs: Available in Coolify dashboard
- Database logs: Monitor for slow queries
- Redis logs: Monitor cache hit rates

## 🚨 Troubleshooting

### Common Issues

**Service Won't Start**
- Check environment variables are set correctly
- Verify Docker image builds successfully
- Review container logs in Coolify

**Database Connection Failed**
- Confirm PostgreSQL container is healthy
- Verify credentials in environment variables
- Check network connectivity between containers

**Redis Connection Issues**
- Check Redis password configuration
- Verify Redis container health
- Monitor memory usage (Redis has 200MB limit)

**Performance Issues**
- Review resource limits in docker-compose.prod.yml
- Monitor database query performance
- Check cache hit rates
- Scale workers if needed (MAX_WORKERS setting)

### Emergency Procedures

**Rollback Deployment**
1. In Coolify, go to deployments history
2. Select previous working version
3. Click "Redeploy"

**Database Recovery**
1. Stop all services
2. Restore from latest backup
3. Restart services
4. Verify data integrity

## 📈 Scaling Considerations

### Horizontal Scaling
- Increase MAX_WORKERS for more concurrent requests
- Consider load balancer for multiple API instances
- Database read replicas for high read loads

### Vertical Scaling
Update resource limits in `.env.production`:
```
API_CPU_LIMIT=2.0
API_MEMORY_LIMIT=2G
DB_MEMORY_LIMIT=1G
```

## 🔄 Maintenance Schedule

### Daily
- Monitor application health
- Check error logs
- Verify backup completion

### Weekly  
- Review performance metrics
- Update dependencies if needed
- Test disaster recovery procedures

### Monthly
- Rotate secrets and passwords
- Review and update monitoring
- Performance optimization review

## 📞 Support

For deployment issues:
1. Check Coolify documentation
2. Review application logs
3. Verify environment configuration
4. Contact system administrator

---

**Last Updated**: June 2025
**Version**: 1.0