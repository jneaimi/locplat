# LocPlat - Simple AI Translation Service

## Overview
LocPlat is a simple AI-powered translation service designed for Directus CMS. It translates English content to Arabic (RTL) and Bosnian (Latin/Cyrillic) using OpenAI and Google Translate with client-provided credentials.

## Features
- **Security First**: Client-provided AI keys per request (never stored)
- **Multiple Providers**: OpenAI (primary) + Google Translate (fallback)
- **Dynamic Fields**: Basic API-configurable field mapping
- **Performance**: Redis caching for cost control
- **Multi-language**: English → Arabic/Bosnian
- **RTL Support**: Proper Arabic text handling
- **Docker Ready**: Coolify compatible deployment

## Architecture
- Single FastAPI service
- PostgreSQL for data persistence
- Redis for caching
- Docker-based deployment

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.9+

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/jneaimi/locplat.git
cd locplat
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Start with Docker Compose:
```bash
docker-compose up -d
```

4. Access the API:
- Health Check: http://localhost:8000/health
- API Documentation: http://localhost:8000/docs

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Translation (Coming Soon)
```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "target_language": "ar",
    "openai_key": "your-openai-key"
  }'
```

## Supported Languages
- **Arabic (ar)**: Full RTL support with cultural sensitivity
- **Bosnian (bs)**: Latin and Cyrillic script support

## Tech Stack
- **Backend**: FastAPI
- **Database**: PostgreSQL
- **Cache**: Redis
- **Deployment**: Docker + Coolify
- **AI Providers**: OpenAI, Google Translate

## Security
- API keys are provided per request and never stored
- Request validation and sanitization
- Rate limiting and caching for cost control

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License
MIT License - see LICENSE file for details

## Support
For issues and questions, please use the GitHub Issues page.