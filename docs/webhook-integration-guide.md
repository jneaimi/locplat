# Directus Webhook Integration Guide

## Overview

The LocPlat webhook system enables automatic translation of content when items are created or updated in Directus CMS. This integration uses Directus Flows to trigger translations and store results in translation collections.

## Architecture

```
Directus CMS → Flow Trigger → Webhook (LocPlat) → AI Translation → Response → Directus Collection
```

## Webhook Endpoints

### Main Translation Webhook
- **URL**: `/api/v1/webhooks/directus/translate`
- **Method**: `POST`
- **Purpose**: Receive content from Directus, translate it, and return structured data

### Validation Endpoint  
- **URL**: `/api/v1/webhooks/directus/validate`
- **Method**: `POST`
- **Purpose**: Validate webhook configuration before setup

### Testing Endpoint
- **URL**: `/api/v1/webhooks/directus/test` 
- **Method**: `POST`
- **Purpose**: Test webhook processing with sample data

### Info Endpoint
- **URL**: `/api/v1/webhooks/directus/info`
- **Method**: `GET`
- **Purpose**: Get setup instructions and configuration examples

## Webhook Request Format

```json
{
  "event": "items.update",
  "collection": "articles",
  "key": "123", 
  "data": {
    "id": 123,
    "title": "Article Title",
    "description": "Article description...",
    "content": {"text": "<p>Article content...</p>"}
  },
  "client_id": "your_client_id",
  "target_language": "ar",
  "provider": "openai",
  "api_key": "sk-your-api-key",
  "source_language": "en",
  "model": "gpt-4",
  "context": "News article translation"
}
```

## Webhook Response Format

```json
{
  "success": true,
  "operation": "upsert",
  "collection": "articles_translations",
  "translated_data": {
    "id": null,
    "articles_id": 123,
    "languages_code": "ar", 
    "title": "عنوان المقال",
    "description": "وصف المقال...",
    "content": {"text": "<p>محتوى المقال...</p>"}
  },
  "metadata": {
    "processing_time_ms": 1250,
    "provider_used": "openai",
    "fields_processed": 3
  }
}
```

## Directus Flow Setup

### 1. Create Event Hook Trigger
- **Type**: Event Hook
- **Collections**: Select your content collection (e.g., `articles`)
- **Actions**: `create`, `update`

### 2. Add Webhook Operation
- **Type**: Webhook
- **Method**: POST
- **URL**: `{{$env.LOCPLAT_WEBHOOK_URL}}/api/v1/webhooks/directus/translate`
- **Headers**: 
  ```json
  {
    "Content-Type": "application/json"
  }
  ```

### 3. Configure Request Body
```json
{
  "event": "{{$trigger.event}}",
  "collection": "{{$trigger.collection}}", 
  "key": "{{$trigger.key}}",
  "data": "{{$trigger.payload}}",
  "client_id": "{{$env.CLIENT_ID}}",
  "target_language": "ar",
  "provider": "openai",
  "api_key": "{{$env.OPENAI_API_KEY}}"
}
```

### 4. Add Response Processing
- **Type**: Create/Update Data
- **Collection**: `{{$last.collection}}` (from webhook response)
- **Data**: `{{$last.translated_data}}`
- **Operation**: `{{$last.operation}}`

## Field Mapping Configuration

Before using webhooks, configure field mapping for your collections:

```bash
# Create field mapping via API
curl -X POST "http://localhost:8000/api/v1/field-mapping/config" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "your_client_id",
    "collection_name": "articles",
    "field_paths": ["title", "description", "content.text"],
    "field_types": {
      "title": "text",
      "description": "textarea", 
      "content.text": "wysiwyg"
    },
    "directus_translation_pattern": "collection_translations",
    "batch_processing": true
  }'
```

## Translation Patterns

### 1. Collection Translations (Recommended)
- **Pattern**: `collection_translations`
- **Result**: Creates records in `{collection}_translations` table
- **Structure**: Standard Directus translation pattern with `languages_code` field

### 2. Language Collections  
- **Pattern**: `language_collections`
- **Result**: Creates records in `{collection}_{language}` tables
- **Structure**: Separate tables per language (e.g., `articles_ar`, `articles_bs`)

## Security

### Webhook Signature Verification
Enable signature verification for production:

```json
{
  "webhook_secret": "your-webhook-secret",
  // ... other fields
}
```

### Environment Variables
Store sensitive data in Directus environment:
- `LOCPLAT_WEBHOOK_URL` - Your LocPlat webhook base URL
- `CLIENT_ID` - Your LocPlat client identifier  
- `OPENAI_API_KEY` - Your OpenAI API key
- `WEBHOOK_SECRET` - Secret for signature verification

## Testing

### 1. Test Configuration
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/directus/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test_client",
    "collection": "articles",
    "provider": "openai",
    "api_key": "sk-your-key",
    "target_language": "ar"
  }'
```

### 2. Test Translation (Dry Run)
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/directus/test" \
  -H "Content-Type: application/json" \
  -d '{
    "sample_data": {
      "title": "Test Article",
      "description": "Test description"
    },
    "client_id": "test_client",
    "collection": "articles", 
    "target_language": "ar",
    "provider": "openai",
    "api_key": "sk-your-key",
    "dry_run": true
  }'
```

## Troubleshooting

### Common Issues

1. **Field mapping not found**
   - Solution: Create field mapping configuration for your collection

2. **Invalid API key**
   - Solution: Verify API key in webhook validation endpoint

3. **Infinite loops**
   - Solution: Translation collections are automatically skipped

4. **Missing translations**
   - Solution: Check field mapping and ensure translatable content exists

### Webhook Logs
Monitor webhook processing through:
- Response metadata (processing time, fields processed)
- Database logs in `field_processing_logs` table
- Directus Flow execution logs

## Performance Optimization

### Batch Processing
Enable batch processing for multiple text fields:
```json
{
  "batch_processing": true
}
```

### Caching
LocPlat automatically caches:
- Field configurations (5 minutes)  
- Translation results (configurable TTL)
- API validation results

### Rate Limiting
Consider implementing rate limiting for high-volume workflows to manage AI provider costs.

## Next Steps

1. ✅ **Webhook endpoints implemented**
2. 🔄 **Set up field mapping** for your collections
3. 🔄 **Create Directus Flow** with webhook integration
4. 🔄 **Test with sample data** using test endpoint
5. 🔄 **Configure webhook security** for production
6. 🔄 **Monitor and optimize** performance

## Support

For issues or questions:
- Check webhook info endpoint: `/api/v1/webhooks/directus/info`
- Review field mapping guide: `/docs/field-mapping-guide.md`
- Test with validation endpoints before production setup
