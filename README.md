# LocPlat - Multi-Language Localization Platform

## Project Overview
LocPlat is a modern, scalable localization platform designed to provide enterprise-grade translation services with support for multiple AI providers, intelligent caching, and dynamic field mapping.

## Key Features
- **Multi-Language Support**: English, Arabic (RTL), Bosnian (Latin/Cyrillic)
- **Multi-Provider AI**: OpenAI, Anthropic, Google Translate, Azure, DeepL
- **Client-Side Credentials**: Secure, zero-knowledge AI credential handling
- **Intelligent Caching**: Multi-level caching for performance optimization
- **Dynamic Field Mapping**: Runtime-configurable translatable field definitions
- **Directus Integration**: Optimized for Directus CMS workflows

## Technology Stack
- **Backend**: FastAPI (Python) with async/await
- **Databases**: PostgreSQL (transactional), MongoDB (configuration)
- **Cache**: Redis Cluster
- **Queue**: RabbitMQ for async processing
- **Containers**: Docker with Kubernetes
- **Monitoring**: Prometheus, Grafana, OpenTelemetry

## Architecture
The platform follows a microservices architecture with the following core services:

1. **Translation Orchestrator** - Main workflow coordinator
2. **AI Provider Adapter** - Unified interface for multiple AI providers
3. **Language Registry** - Language profiles and configurations
4. **Field Mapper** - Dynamic field discovery and mapping
5. **Cache Manager** - Multi-level caching system
6. **Quality Validator** - Translation quality assessment
7. **Security Manager** - Credential handling and audit logging
8. **Analytics Engine** - Metrics and performance monitoring

## Development Phases
- **Phase 1**: Core Foundation (6-8 weeks)
- **Phase 2**: Multi-Provider Ecosystem (6-8 weeks)
- **Phase 3**: Enterprise Features (8-10 weeks)
- **Phase 4**: Advanced Capabilities (8-10 weeks)

## Getting Started
1. Clone the repository
2. Initialize Task Master: `taskmaster init`
3. Start with Task #1: "Setup Core Project Infrastructure"
4. Follow the dependency chain for optimal development flow

## Task Management
This project uses Task Master for project management. Key commands:
- `taskmaster next` - Get the next task to work on
- `taskmaster status <id> <status>` - Update task status
- `taskmaster get <id>` - Get detailed task information
- `taskmaster tasks` - View all tasks

## Current Status
Project initialized with comprehensive PRD and 13 main tasks with detailed subtasks.
Ready to begin development with Task #1.

**New Addition**: Task #13 - Coolify Deployment Configuration for easy deployment!

## Documentation
- `/scripts/prd.txt` - Complete Product Requirements Document
- `/tasks/` - Individual task files with detailed specifications
- `/docs/` - Technical documentation (to be created)

## Support Languages (Initial)
- **English** (en) - Source language, international variant
- **Arabic** (ar) - RTL support, formal register, cultural context
- **Bosnian** (bs) - Latin script primary, optional Cyrillic support

## AI Providers (Planned)
- **OpenAI** - GPT-4, GPT-3.5 (Primary for Arabic & English)
- **Anthropic** - Claude-3 models (High accuracy)
- **Google Translate** - V3 API (Cost-effective, wide language support)
- **Azure Translator** - Enterprise features, compliance
- **DeepL** - European languages, natural sounding

## Security & Compliance
- Zero-knowledge credential architecture
- Client-side AI API key management
- Comprehensive audit logging
- GDPR and SOC 2 compliance ready
- End-to-end encryption for data in transit
