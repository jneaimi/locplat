#!/bin/bash

# =============================================================================
# LocPlat Production Configuration Validator
# =============================================================================

set -e

echo "🔍 LocPlat Production Configuration Validator"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ .env.production file not found!${NC}"
    echo "📝 Please copy .env.production.template to .env.production"
    echo "   cp .env.production.template .env.production"
    exit 1
fi

echo -e "${GREEN}✅ .env.production file found${NC}"

# Load environment variables
set -a
source .env.production
set +a

# Validation functions
validate_not_placeholder() {
    local var_name=$1
    local var_value=$2
    local placeholder_pattern=$3
    
    if [[ $var_value =~ $placeholder_pattern ]]; then
        echo -e "${RED}❌ $var_name contains placeholder value${NC}"
        echo "   Please replace with actual value"
        return 1
    else
        echo -e "${GREEN}✅ $var_name is configured${NC}"
        return 0
    fi
}

validate_length() {
    local var_name=$1
    local var_value=$2
    local min_length=$3
    
    if [ ${#var_value} -lt $min_length ]; then
        echo -e "${RED}❌ $var_name is too short (minimum $min_length characters)${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $var_name meets length requirement${NC}"
        return 0
    fi
}

# Start validation
echo ""
echo "🔐 Security Configuration Validation"
echo "====================================="

ERRORS=0

# Validate SECRET_KEY
if ! validate_not_placeholder "SECRET_KEY" "$SECRET_KEY" "GENERATE.*REPLACE"; then
    ERRORS=$((ERRORS + 1))
fi
if ! validate_length "SECRET_KEY" "$SECRET_KEY" 32; then
    ERRORS=$((ERRORS + 1))
fi

# Validate WEBHOOK_SECRET
if ! validate_not_placeholder "WEBHOOK_SECRET" "$WEBHOOK_SECRET" "GENERATE.*REPLACE"; then
    ERRORS=$((ERRORS + 1))
fi
if ! validate_length "WEBHOOK_SECRET" "$WEBHOOK_SECRET" 32; then
    ERRORS=$((ERRORS + 1))
fi

# Validate POSTGRES_PASSWORD
if ! validate_not_placeholder "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD" "REPLACE.*PASSWORD"; then
    ERRORS=$((ERRORS + 1))
fi
if ! validate_length "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD" 16; then
    ERRORS=$((ERRORS + 1))
fi

# Validate REDIS_PASSWORD
if ! validate_not_placeholder "REDIS_PASSWORD" "$REDIS_PASSWORD" "REPLACE.*PASSWORD"; then
    ERRORS=$((ERRORS + 1))
fi
if ! validate_length "REDIS_PASSWORD" "$REDIS_PASSWORD" 16; then
    ERRORS=$((ERRORS + 1))
fi

# Check ENVIRONMENT is set to production
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${GREEN}✅ ENVIRONMENT is set to production${NC}"
else
    echo -e "${RED}❌ ENVIRONMENT must be set to 'production'${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Validate CORS_ORIGINS doesn't contain localhost
if [[ $CORS_ORIGINS == *"localhost"* ]]; then
    echo -e "${YELLOW}⚠️  CORS_ORIGINS contains localhost (should be production domains)${NC}"
fi

echo ""
echo "🐳 Docker Configuration Validation"
echo "==================================="

# Test docker-compose.prod.yml syntax
if docker-compose -f docker-compose.prod.yml config > /dev/null 2>&1; then
    echo -e "${GREEN}✅ docker-compose.prod.yml syntax is valid${NC}"
else
    echo -e "${RED}❌ docker-compose.prod.yml has syntax errors${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Final results
echo ""
echo "📊 Validation Results"
echo "==================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 All validations passed! Ready for deployment.${NC}"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Upload your repository to Coolify"
    echo "2. Set docker-compose.prod.yml as the build file"
    echo "3. Copy environment variables to Coolify"
    echo "4. Deploy and monitor health checks"
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS validation error(s)${NC}"
    echo ""
    echo "📝 Please fix the issues above before deploying to production."
    exit 1
fi