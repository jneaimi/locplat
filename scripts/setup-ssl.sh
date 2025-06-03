#!/bin/bash

# Coolify SSL Setup Script for LocPlat
echo "🔒 Coolify SSL Configuration for LocPlat"
echo "========================================"

# Check if running on Coolify server
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Run this on your Coolify server."
    exit 1
fi

# Check current proxy status
echo "📋 Current Coolify Proxy Status:"
docker ps --filter name=coolify-proxy --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔍 Current LocPlat Container:"
docker ps --filter name=api-eoc084sskc8cowswosssg4c8 --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "📝 Required Environment Variables for Coolify:"
echo "=============================================="
echo "DOMAIN_NAME=locplat.estatfinder.com"
echo "LETSENCRYPT_EMAIL=your-email@domain.com"
echo "VIRTUAL_HOST=locplat.estatfinder.com"
echo "VIRTUAL_PORT=8000"

echo ""
echo "🚀 Next Steps:"
echo "1. Add environment variables above in Coolify dashboard"
echo "2. Add domain 'locplat.estatfinder.com' in Coolify domain settings"
echo "3. Enable SSL certificate generation"
echo "4. Redeploy the service"
echo "5. Test: curl https://locplat.estatfinder.com/health"

echo ""
echo "🔧 Manual SSL Certificate Check:"
echo "================================"
echo "# Check if Let's Encrypt cert exists:"
echo "docker exec coolify-proxy ls -la /data/caddy/certificates/"
echo ""
echo "# Check Caddy configuration:"
echo "docker exec coolify-proxy cat /etc/caddy/Caddyfile"
echo ""
echo "# Check SSL certificate for your domain:"
echo "echo | openssl s_client -connect locplat.estatfinder.com:443 -servername locplat.estatfinder.com"