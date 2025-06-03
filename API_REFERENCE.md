# LocPlat API Reference

## Overview

LocPlat is a comprehensive AI-powered translation service designed for Directus CMS integration. 
This API provides intelligent translation capabilities with multiple AI providers, advanced caching, 
and seamless Directus workflow integration.

**Base URL:** `http://localhost:8000` (Development) | `https://your-domain.com` (Production)
**API Version:** `v1`
**API Documentation:** Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

---

## Authentication & Security

### API Key Security
- **Zero Storage Policy**: API keys are never stored or logged
- **Per-Request Keys**: API keys must be provided with each request
- **Provider-Specific**: Each AI provider requires its own valid API key

### CORS Configuration
- Configurable allowed origins, methods, and headers
- Production-ready security settings

---

## Core Translation API

### Base Path: `/api/v1/translate`

#### **POST** `/api/v1/translate/`
**Translate single text with flexible provider selection**

**Request Body:**
```json
{
  "text": "Hello, world!",
  "source_lang": "en",
  "target_lang": "ar",
  "provider": "openai",
  "api_key": "your-openai-api-key"
}
```

**Parameters:**
- `text` (string, required): Text to translate
- `source_lang` (string, required): Source language code
- `target_lang` (string, required): Target language code
- `provider` (string, required): AI provider ("openai", "anthropic", "mistral", "deepseek")
- `api_key` (string, required): Provider API key
- `model` (string, optional): Specific model name
- `context` (string, optional): Additional context

**Response:**
```json
{
  "translated_text": "مرحبا بالعالم!",
  "provider_used": "openai",
  "model_used": "gpt-4o-mini",
  "source_lang": "en",
  "target_lang": "ar",
  "quality_score": 0.95,
  "language_direction": "rtl",
  "metadata": {
    "processing_time_ms": 850,
    "cache_hit": false,
    "display_options": {
      "terminal_rtl": "‮مرحبا بالعالم!‬",
      "html_rtl": "<div dir=\"rtl\">مرحبا بالعالم!</div>",
      "css_attributes": "dir=\"rtl\" style=\"text-align: right;\""
    }
  }
}
```

---

#### **POST** `/api/v1/translate/batch`
**Translate multiple texts efficiently**

**Request Body:**
```json
{
  "texts": ["Hello", "World", "Welcome"],
  "source_lang": "en",
  "target_lang": "ar",
  "provider": "anthropic",
  "api_key": "your-anthropic-api-key",
  "model": "claude-3-sonnet-20240229",
  "context": "Website navigation items"
}
```

**Response:**
```json
{
  "results": [
    {
      "translated_text": "مرحبا",
      "provider_used": "anthropic",
      "model_used": "claude-3-sonnet-20240229",
      "source_lang": "en",
      "target_lang": "ar",
      "quality_score": 0.98,
      "language_direction": "rtl",
      "metadata": {}
    }
  ],
  "total_translations": 3,
  "successful_translations": 3,
  "provider_used": "anthropic",
  "model_used": "claude-3-sonnet-20240229"
}
```

**Parameters:** Same as single translation, but with `texts` array instead of `text`
- `provider` (string, required): AI provider ("openai", "anthropic", "mistral", "deepseek")
- `api_key` (string, required): Provider API key
- `model` (string, optional): Specific model name
- `context` (string, optional): Additional context

**Response:**
```json
{
  "translated_text": "مرحبا بالعالم!",
  "provider_used": "openai",
  "model_used": "gpt-4o-mini",
  "source_lang": "en",
  "target_lang": "ar",
  "quality_score": 0.95,
  "language_direction": "rtl",
  "metadata": {
    "processing_time_ms": 850,
    "cache_hit": false,
    "display_options": {
      "terminal_rtl": "‮مرحبا بالعالم!‬",
      "html_rtl": "<div dir=\"rtl\">مرحبا بالعالم!</div>",
      "css_attributes": "dir=\"rtl\" style=\"text-align: right;\""
    }
  }
}
```

---

#### **POST** `/api/v1/translate/batch`
**Translate multiple texts efficiently**

**Request Body:**
```json
{
  "texts": ["Hello", "World", "Welcome"],
  "source_lang": "en",
  "target_lang": "ar",
  "provider": "anthropic",
  "api_key": "your-anthropic-api-key"
}
```

**Response:**
```json
{
  "results": [
    {
      "translated_text": "مرحبا",
      "provider_used": "anthropic",
      "source_lang": "en",
      "target_lang": "ar",
      "quality_score": 0.98,
      "language_direction": "rtl"
    }
  ],
  "total_translations": 3,
  "successful_translations": 3
}
```
- `provider` (string, required): AI provider ("openai", "anthropic", "mistral", "deepseek")
- `api_key` (string, required): Provider API key
- `model` (string, optional): Specific model name
- `context` (string, optional): Additional context

**Response:**
```json
{
  "translated_text": "مرحبا بالعالم!",
  "provider_used": "openai",
  "model_used": "gpt-4o-mini",
  "source_lang": "en",
  "target_lang": "ar",
  "quality_score": 0.95,
  "language_direction": "rtl",
  "metadata": {
    "processing_time_ms": 850,
    "cache_hit": false,
    "display_options": {
      "terminal_rtl": "‮مرحبا بالعالم!‬",
      "html_rtl": "<div dir=\"rtl\">مرحبا بالعالم!</div>",
      "css_attributes": "dir=\"rtl\" style=\"text-align: right;\""
    }
  }
}
```

---

#### **POST** `/api/v1/translate/batch`
**Translate multiple texts efficiently**

**Request Body:**
```json
{
  "texts": ["Hello", "World", "Welcome"],
  "source_lang": "en",
  "target_lang": "ar",
  "provider": "anthropic",
  "api_key": "your-anthropic-api-key"
}
```

**Response:**
```json
{
  "results": [
    {
      "translated_text": "مرحبا",
      "provider_used": "anthropic",
      "source_lang": "en",
      "target_lang": "ar",
      "quality_score": 0.98,
      "language_direction": "rtl"
    }
  ],
  "total_translations": 3,
  "successful_translations": 3
}
```
- `provider` (string, required): AI provider
- `api_key` (string, required): Provider API key
- `model` (string, optional): Specific model name
- `context` (string, optional): Additional context

**Response:**
```json
{
  "translated_text": "مرحبا بالعالم!",
  "provider_used": "openai",
  "model_used": "gpt-4o-mini",
  "source_lang": "en",
  "target_lang": "ar",
  "quality_score": 0.95,
  "language_direction": "rtl",
  "metadata": {
    "processing_time_ms": 850,
    "cache_hit": false
  }
}
```

---

#### **POST** `/api/v1/translate/batch`
**Translate multiple texts efficiently**

**Request Body:**
```json
{
  "texts": ["Hello", "World", "Welcome"],
  "source_lang": "en",
  "target_lang": "ar",
  "provider": "anthropic",
  "api_key": "your-anthropic-api-key"
}
```

**Response:**
```json
{
  "results": [{
    "translated_text": "مرحبا",
    "provider_used": "anthropic",
    "source_lang": "en",
    "target_lang": "ar",
    "quality_score": 0.98,
    "language_direction": "rtl"
  }],
  "total_translations": 3,
  "successful_translations": 3
}
```
- `provider` (string, required): AI provider
- `api_key` (string, required): Provider API key
- `model` (string, optional): Specific model name
- `context` (string, optional): Additional context

**Response:** Translation response with RTL display helpers for Arabic

---

#### **POST** `/api/v1/translate/batch`
**Translate multiple texts efficiently**

**Request Body:**
```json
{
  "texts": ["Hello", "World", "Welcome"],
  "source_lang": "en",
  "target_lang": "ar",
  "provider": "anthropic",
  "api_key": "your-anthropic-api-key"
}
```

**Response:** Array of translation results

---

#### **POST** `/api/v1/translate/structured`
**Translate structured content with field mapping**

**Request Body:**
```json
{
  "content": {
    "title": "Welcome to Our Platform",
    "description": "Comprehensive AI translation service",
    "slug": "welcome-platform",
    "status": "published"
  },
  "client_id": "directus-client-1",
  "collection_name": "articles",
  "source_lang": "en",
  "target_lang": "ar",
  "provider": "openai",
  "api_key": "your-openai-api-key"
}
```

**Response:** Translated content with field mapping applied

---

#### **POST** `/api/v1/translate/preview`
**Preview translatable fields without translating**

Shows which fields would be translated based on field mapping configuration.

---

#### **POST** `/api/v1/translate/validate`
**Validate translation request before processing**

Checks field mapping, provider availability, API key validity, and language support.
---

## Provider & Language Information

#### **GET** `/api/v1/translate/providers`
**Get available providers and supported models**

Returns list of AI providers and their model configurations.

#### **GET** `/api/v1/translate/languages/{provider}`
**Get supported languages for a specific provider**

Returns supported language codes for the specified provider.

#### **GET** `/api/v1/translate/language-pairs/{provider}`
**Get detailed language pairs and capabilities**

Returns comprehensive information about language pairs, features, and provider capabilities.

#### **GET** `/api/v1/translate/language-direction/{lang_code}`
**Get text direction for a language code**

Returns whether a language is LTR or RTL.

#### **POST** `/api/v1/translate/validate/{provider}`
**Validate API key for a specific provider**

Checks if the provided API key is valid for the specified provider.

---

## Service Monitoring & Analytics

#### **GET** `/api/v1/translate/metrics`
**Get comprehensive service metrics**

Returns service health, performance statistics, provider metrics, and cache information.

#### **GET** `/api/v1/translate/history`
**Get translation history with filtering**

Query Parameters:
- `client_id`, `provider`, `start_date`, `end_date`
- `content_type`, `status`, `limit`, `offset`

Returns paginated translation history records.

---

## Field Mapping API

### Base Path: `/api/v1/field-mapping`

#### **POST** `/api/v1/field-mapping/config`
**Create or update field mapping configuration**

Configure which fields should be translated for specific client/collection combinations.

#### **GET** `/api/v1/field-mapping/config/{client_id}/{collection_name}`
**Get field mapping configuration**

Retrieve existing field mapping configuration.

#### **DELETE** `/api/v1/field-mapping/config/{client_id}/{collection_name}`
**Delete field mapping configuration**

Remove field mapping configuration.

#### **GET** `/api/v1/field-mapping/patterns`
**Get available translation patterns**

Returns predefined field mapping patterns like "directus_standard".
---

## Webhook API (Directus Integration)

### Base Path: `/api/v1/webhooks`

#### **POST** `/api/v1/webhooks/directus`
**Process Directus webhook for automatic translation**

Automatically translates content when Directus items are created or updated.

**Request Headers:**
- `X-Directus-Signature` (optional): Webhook signature
- `Content-Type`: `application/json`

**Request Body:**
```json
{
  "event": "items.create",
  "collection": "articles",
  "key": 123,
  "data": {
    "title": "Welcome to Our Platform",
    "description": "Comprehensive AI translation service"
  },
  "client_id": "directus-client-1",
  "target_language": "ar",
  "provider": "openai",
  "api_key": "your-openai-api-key"
}
```

#### **POST** `/api/v1/webhooks/batch`
**Process batch webhook for multiple items**

Handles bulk translation operations for multiple Directus items.

---

## Cache Management API

### Base Path: `/api/v1/cache`

#### **GET** `/api/v1/cache/info`
**Get cache information and statistics**

Returns Redis cache status, memory usage, hit rates, and performance metrics.

#### **GET** `/api/v1/cache/stats`
**Get detailed cache statistics**

Provides comprehensive cache performance analytics.

#### **DELETE** `/api/v1/cache/clear`
**Clear all cache entries**

Removes all cached translations.

#### **DELETE** `/api/v1/cache/pattern/{pattern}`
**Clear cache entries matching pattern**

Removes cache entries matching specific patterns.

---

## Health Check API

#### **GET** `/health`
**Get service health status**

Returns overall service health, dependency status, and system metrics.
---

## Error Responses

### Standard Error Format
```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "TRANSLATION_FAILED", 
  "timestamp": "2024-01-01T12:00:00.123Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Common HTTP Status Codes
- **200 OK**: Request successful
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Invalid API key
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

### Error Codes
- `INVALID_API_KEY`: API key is invalid or missing
- `UNSUPPORTED_LANGUAGE`: Language not supported by provider
- `TRANSLATION_FAILED`: Translation process failed
- `CACHE_ERROR`: Cache operation failed
- `FIELD_MAPPING_NOT_FOUND`: Field mapping configuration not found
- `PROVIDER_UNAVAILABLE`: AI provider is temporarily unavailable
- `RATE_LIMIT_EXCEEDED`: Too many requests

---

## Rate Limiting

- **Default Limits**: 100 requests per minute per client
- **Burst Limit**: 20 requests per 10 seconds
- **Headers**: `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **Configurable**: Limits can be adjusted per client

---

## Best Practices

### API Key Management
- Never store API keys in client-side code
- Use environment variables for API keys
- Rotate API keys regularly
- Monitor API key usage

### Request Optimization
- Use batch endpoints for multiple translations
- Implement client-side caching for repeated content
- Use appropriate context for better translations
- Monitor translation quality scores

### Error Handling
- Implement retry logic with exponential backoff
- Handle rate limiting gracefully
- Log errors for debugging
- Provide fallback mechanisms

### Performance
- Use structured translation for complex content
- Cache frequently requested translations
- Monitor service metrics regularly
- Use appropriate models for your use case
---

## SDKs and Examples

### cURL Examples

**Single Translation:**
```bash
curl -X POST "http://localhost:8000/api/v1/translate/" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "source_lang": "en", 
    "target_lang": "ar",
    "provider": "openai",
    "api_key": "your-api-key"
  }'
```

**Batch Translation:**
```bash
curl -X POST "http://localhost:8000/api/v1/translate/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello", "World"],
    "source_lang": "en",
    "target_lang": "ar", 
    "provider": "openai",
    "api_key": "your-api-key"
  }'
```

### JavaScript/TypeScript
```typescript
interface TranslationRequest {
  text: string;
  source_lang: string;
  target_lang: string;
  provider: string;
  api_key: string;
  model?: string;
  context?: string;
}

async function translateText(request: TranslationRequest) {
  const response = await fetch('/api/v1/translate/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error(`Translation failed: ${response.statusText}`);
  }
  
  return await response.json();
}
```

### Python
```python
import requests
from typing import Dict, Any

def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    provider: str,
    api_key: str,
    base_url: str = "http://localhost:8000",
    model: str = None,
    context: str = None
) -> Dict[str, Any]:
    
    payload = {
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "provider": provider,
        "api_key": api_key
    }
    
    if model:
        payload["model"] = model
    if context:
        payload["context"] = context
    
    response = requests.post(
        f"{base_url}/api/v1/translate/",
        json=payload
    )
    
    response.raise_for_status()
    return response.json()
```
---

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- Multi-provider AI translation support (OpenAI, Anthropic, Mistral, DeepSeek)
- Directus CMS integration with webhooks
- Field mapping configuration system
- Advanced Redis caching with intelligent TTL
- RTL language support with display helpers
- Comprehensive webhook system for automation
- Service monitoring and analytics
- Batch translation capabilities
- Structured content translation with field mapping

---

## Support

- **Documentation**: `/docs` endpoint for interactive API documentation  
- **Issues**: GitHub Issues for bug reports and feature requests
- **API Help**: Interactive documentation at `/docs` endpoint
- **Status Page**: `/health` endpoint for service status
- **Real-time Metrics**: `/api/v1/translate/metrics` for performance monitoring

---

## Security Features

- **Zero API Key Storage**: Keys provided per request, never persisted
- **Input Sanitization**: Comprehensive validation and cleaning
- **Rate Limiting**: Configurable request throttling per client
- **Request Isolation**: Stateless architecture for security
- **Error Handling**: Secure error messages without data leakage
- **CORS Configuration**: Production-ready cross-origin settings

---

## Supported Languages

### **Arabic (ar)**
- Full RTL (Right-to-Left) support with proper display formatting
- Cultural sensitivity and context awareness
- Proper Arabic typography and text direction
- Terminal and HTML display helpers included

### **Bosnian (bs)**
- Latin and Cyrillic script support
- Regional dialect awareness
- Cultural context preservation
- European language optimization

### **English (en)**
- Primary source language
- Comprehensive context understanding
- Technical and creative content support

---

## Provider Comparison

| Feature | OpenAI | Anthropic | Mistral | DeepSeek |
|---------|--------|-----------|---------|----------|
| **Speed** | Fast | Medium | Fast | Medium |
| **Quality** | High | Very High | High | Good |
| **Context** | 128K | 200K | 32K | 64K |
| **Cost** | Medium | High | Low | Very Low |
| **RTL Support** | Excellent | Excellent | Good | Good |
| **Best For** | General use | Creative content | European langs | High volume |

---

*This API reference is automatically generated and updated. For the most current information, please refer to the interactive documentation at `/docs`.*

---

**LocPlat** - Intelligent AI Translation for Modern Content Management Systems
