# LocPlat - AI Translation Service

## Overview
LocPlat is a comprehensive AI-powered translation service designed for Directus CMS integration. It provides intelligent translation capabilities with multiple AI providers, advanced caching, and seamless Directus workflow integration.

## 🚀 Key Features

### **Multi-Provider AI Translation**
- **Primary Providers**: OpenAI, Anthropic, Mistral, DeepSeek
- **Cascading Fallback**: Automatic provider switching on failures
- **Client-Provided Keys**: API keys provided per request (never stored)
- **Model Selection**: Choose specific models per provider

### **Directus CMS Integration**
- **Native Integration**: Seamless Directus workflow support
- **Field Mapping**: Intelligent field configuration for translation
- **Webhook Support**: Real-time translation triggers
- **Batch Processing**: Efficient bulk content translation
- **Schema Introspection**: Automatic field type detection

### **Advanced Features**
- **RTL Language Support**: Full Arabic text handling with proper directionality
- **HTML Preservation**: Maintains markup structure during translation
- **Intelligent Caching**: Redis-based caching with cost-aware TTL
- **Content Processing**: Smart text extraction and formatting
- **Quality Scoring**: Translation quality assessment

### **Security & Performance**
- **Zero Storage**: API keys never stored or logged
- **Rate Limiting**: Configurable request throttling
- **Input Validation**: Comprehensive security measures
- **Performance Monitoring**: Request timing and success metrics

## 📁 Project Structure

```
locplat/
├── app/                    # Main application
│   ├── api/               # API endpoints
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
├── scripts/               # Utility scripts and setup tools
├── tests/                 # Test files and debugging tools
├── docs/                  # Documentation
├── tasks/                 # TaskMaster project management
├── docker-compose.yml     # Development environment
├── docker-compose.prod.yml # Production environment
└── requirements.txt       # Python dependencies
```

## 🏃‍♂️ Quick Start

### Development Setup

1. **Clone the repository**:
```bash
git clone https://github.com/your-repo/locplat.git
cd locplat
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start with Docker Compose**:
```bash
docker-compose up -d
```

4. **Access the application**:
- **API Health**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Redis Commander**: http://localhost:8081
- **pgAdmin**: http://localhost:5050

### Production Deployment

1. **Prepare production environment**:
```bash
cp .env.production.template .env.production
# Configure production values
```

2. **Validate configuration**:
```bash
./scripts/validate-production-config.sh
```

3. **Deploy with Coolify**:
- Upload project with `docker-compose.prod.yml`
- Configure environment variables
- Deploy and monitor

📖 **Complete deployment guide**: [DEPLOYMENT.md](DEPLOYMENT.md)

## 🔧 API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Single Text Translation
```bash
curl -X POST "http://localhost:8000/api/v1/translate/" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "source_lang": "en",
    "target_lang": "ar",
    "provider": "openai",
    "api_key": "your-openai-api-key",
    "context": "Greeting message"
  }'
```

### Batch Translation
```bash
curl -X POST "http://localhost:8000/api/v1/translate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello", "World", "Welcome"],
    "source_lang": "en",
    "target_lang": "ar",
    "provider": "anthropic",
    "api_key": "your-anthropic-api-key"
  }'
```

### Structured Content Translation
```bash
curl -X POST "http://localhost:8000/api/v1/translate/structured" \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "title": "Welcome",
      "description": "This is a test"
    },
    "client_id": "your-client-id",
    "collection_name": "articles",
    "source_lang": "en",
    "target_lang": "ar",
    "provider": "openai",
    "api_key": "your-api-key"
  }'
```

### Available Providers
```bash
curl http://localhost:8000/api/v1/translate/providers
```

## 🌐 Supported Languages

### **Arabic (ar)**
- Full RTL (Right-to-Left) support
- Cultural sensitivity and context awareness
- Proper Arabic typography and formatting

### **Bosnian (bs)**
- Latin and Cyrillic script support
- Regional dialect awareness
- Cultural context preservation

## 🛠 Tech Stack

### **Backend**
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for intelligent caching
- **AI Providers**: OpenAI, Anthropic, Mistral, DeepSeek

### **Infrastructure**
- **Containerization**: Docker & Docker Compose
- **Deployment**: Coolify compatible
- **Monitoring**: Built-in performance metrics
- **Documentation**: Auto-generated OpenAPI specs

### **Development Tools**
- **Testing**: Pytest with comprehensive test coverage
- **Project Management**: TaskMaster AI integration
- **Code Quality**: Type hints and validation
- **Environment**: Development and production configurations

## 🔒 Security Features

- **Zero API Key Storage**: Keys provided per request, never persisted
- **Input Sanitization**: Comprehensive validation and cleaning
- **Rate Limiting**: Configurable request throttling
- **Request Isolation**: Stateless architecture
- **Error Handling**: Secure error messages without data leakage

## 📊 Performance & Monitoring

- **Intelligent Caching**: Cost-aware TTL strategies
- **Request Metrics**: Success rates, response times
- **Provider Statistics**: Performance tracking per AI provider
- **Quality Scoring**: Translation quality assessment
- **Resource Monitoring**: Memory and CPU usage tracking

## 🧪 Testing

### Run Tests
```bash
# Run all tests
docker-compose exec app pytest

# Run specific test categories
pytest tests/test_translation_providers.py
pytest tests/test_cache_integration.py
```

### Test Coverage
The project includes comprehensive testing for:
- AI provider integrations
- Caching mechanisms
- Field mapping functionality
- API endpoints
- Directus integration

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Field Mapping**: Configuration examples in `/docs`
- **TaskMaster Tasks**: Project management in `/tasks`

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Run tests**: `pytest tests/`
4. **Commit changes**: `git commit -m 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Guidelines
- Follow Python PEP 8 style guidelines
- Add tests for new functionality
- Update documentation as needed
- Use type hints for better code clarity

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: Check `/docs` for detailed guides
- **API Help**: Interactive documentation at `/docs` endpoint

## 🎯 Roadmap

- [ ] Additional AI providers integration
- [ ] Enhanced Directus workflow automation
- [ ] Advanced translation quality metrics
- [ ] Multi-tenant support
- [ ] Real-time translation streaming

---

**LocPlat** - Intelligent AI Translation for Modern Content Management Systems
