#!/bin/bash

# =============================================================================
# LocPlat Coolify Deployment Helper Script
# =============================================================================

echo "🚀 LocPlat Coolify Deployment Helper"
echo "======================================"

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "❌ ERROR: .env.production file not found!"
    echo "Please ensure you're in the project root directory."
    exit 1
fi

# Validate environment variables
echo "🔍 Validating environment configuration..."

# Check for placeholder values
if grep -q "change_this_to_a_secure" .env.production; then
    echo "❌ ERROR: Found placeholder values in .env.production"
    echo "Please replace all 'change_this_to_a_secure' values with actual secure passwords"
    exit 1
fi

echo "✅ Environment validation passed"

# Instructions for Coolify deployment
echo ""
echo "📋 Coolify Deployment Instructions:"
echo "====================================="
echo ""
echo "1. In Coolify, create a new Docker Compose service"
echo "2. Set the following configuration:"
echo "   - Repository: Your Git repository URL"
echo "   - Branch: main (or your production branch)"
echo "   - Docker Compose File: docker-compose.prod.yml"
echo "   - Environment File: .env.production"
echo ""
echo "3. Environment Variables to set in Coolify:"
echo "   (These override .env.production for security)"
echo ""
echo "   🔐 Required Security Variables:"
echo "   - SECRET_KEY=<your-32-char-secret>"
echo "   - WEBHOOK_SECRET=<your-32-char-secret>"
echo "   - POSTGRES_PASSWORD=<your-secure-db-password>"
echo "   - REDIS_PASSWORD=<your-secure-redis-password>"
echo ""
echo "   🌐 Domain Configuration:"
echo "   - ALLOWED_HOSTS=yourdomain.com,*.yourdomain.com"
echo "   - CORS_ORIGINS=https://yourdomain.com"
echo ""
echo "4. Port Configuration:"
echo "   - Set API_PORT=8000 (or your preferred port)"
echo ""
echo "5. Health Check URLs:"
echo "   - Main: http://localhost:8000/health"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "🔧 Resource Recommendations:"
echo "============================="
echo "Minimum for production:"
echo "- CPU: 1 vCPU"
echo "- RAM: 2GB"
echo "- Storage: 10GB SSD"
echo ""
echo "🚨 Security Notes:"
echo "=================="
echo "1. Never commit real passwords to Git"
echo "2. Use Coolify's environment variable override feature"
echo "3. Enable HTTPS/SSL for your domain"
echo "4. Consider using a managed PostgreSQL service"
echo ""
echo "✅ Your .env.production file is ready for Coolify deployment!"
echo ""
echo "Next steps:"
echo "1. Push your code to Git repository"
echo "2. Create the service in Coolify"
echo "3. Set environment variables in Coolify UI"
echo "4. Deploy and monitor the logs"
echo ""