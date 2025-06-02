# Field Mapping System - Usage Examples

## Overview
The Field Mapping System enables LocPlat to automatically extract and process translatable content from Directus CMS collections, supporting various content types and translation patterns.

## Basic Configuration

### 1. Configure Field Paths
```python
# Example Directus collection structure
directus_article = {
    "id": 1,
    "title": "Article Title",
    "content": "<p>Rich text content</p>",
    "summary": "Brief summary",
    "metadata": {
        "description": "SEO description",
        "keywords": ["keyword1", "keyword2"]
    },
    "translations": []
}

# Field configuration
field_config = {
    "client_id": "my-directus-site",
    "collection_name": "articles",
    "field_paths": [
        "title",
        "content", 
        "summary",
        "metadata.description"
    ],
    "field_types": {
        "title": "text",
        "content": "wysiwyg",
        "summary": "textarea",
        "metadata.description": "text"
    },
    "directus_translation_pattern": "collection_translations",
    "batch_processing": false,
    "preserve_html_structure": true
}
```

### 2. API Usage

#### Create/Update Configuration
```bash
curl -X POST "http://localhost:8000/api/v1/field-mapping/config" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "my-directus-site",
    "collection_name": "articles",
    "field_paths": ["title", "content", "summary"],
    "field_types": {
      "title": "text",
      "content": "wysiwyg",
      "summary": "textarea"
    },
    "directus_translation_pattern": "collection_translations"
  }'
```

#### Extract Fields for Translation
```bash
curl -X POST "http://localhost:8000/api/v1/field-mapping/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "my-directus-site",
    "collection_name": "articles",
    "content": {
      "id": 1,
      "title": "My Article Title",
      "content": "<p>Article content with <strong>HTML</strong></p>",
      "summary": "Article summary"
    },
    "language": "ar"
  }'
```

## Advanced Configurations

### RTL Language Support
```python
field_config_with_rtl = {
    "client_id": "my-directus-site",
    "collection_name": "articles",
    "field_paths": ["title", "content"],
    "rtl_field_mapping": {
        "ar": {
            "field_paths": ["title", "content"],
            "custom_processing": True
        }
    }
}
```

### Batch Processing
```python
batch_config = {
    "client_id": "my-directus-site", 
    "collection_name": "articles",
    "field_paths": ["title", "summary", "excerpt"],
    "batch_processing": True,  # Groups text fields for efficient translation
    "field_types": {
        "title": "text",
        "summary": "text", 
        "excerpt": "text"
    }
}
```

### Directus Translation Patterns

#### Pattern 1: collection_translations (Standard)
```python
# For articles -> articles_translations pattern
translation_config = {
    "directus_translation_pattern": "collection_translations",
    "is_translation_collection": False,
    "primary_collection": "articles"
}

# Resulting structure:
# articles_translations table:
# - id (auto)
# - articles_id (FK)
# - languages_code (e.g., 'ar', 'bs')  
# - title (translated)
# - content (translated)
```

#### Pattern 2: language_collections  
```python
# For articles_en, articles_ar, articles_bs pattern
language_config = {
    "directus_translation_pattern": "language_collections",
    "is_translation_collection": True,
    "primary_collection": "articles"
}
```

## Content Types

### HTML/WYSIWYG Processing
```python
html_content = {
    "content": "<div><h2>Section Title</h2><p>Paragraph with <a href='#'>link</a></p></div>"
}

# The system will:
# 1. Detect HTML content type
# 2. Extract text nodes for translation
# 3. Preserve HTML structure and attributes
# 4. Reassemble with translated text
```

### JSON Field Processing
```python
json_content = {
    "metadata": {
        "seo": {
            "title": "SEO Title",
            "description": "SEO Description"
        }
    }
}

# Configure nested paths:
field_paths = [
    "metadata.seo.title",
    "metadata.seo.description"
]
```

## Integration Examples

### Python Client Integration
```python
import httpx
import asyncio

class LocPlatFieldMapper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def configure_collection(self, client_id: str, collection_name: str, 
                                 field_paths: list, field_types: dict = None):
        """Configure field mapping for a collection."""
        config = {
            "client_id": client_id,
            "collection_name": collection_name,
            "field_paths": field_paths,
            "field_types": field_types or {}
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/field-mapping/config",
            json=config
        )
        return response.json()
    
    async def extract_translatable_fields(self, client_id: str, 
                                        collection_name: str, content: dict):
        """Extract fields ready for translation."""
        request = {
            "client_id": client_id,
            "collection_name": collection_name,
            "content": content
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/field-mapping/extract", 
            json=request
        )
        return response.json()

# Usage
async def main():
    mapper = LocPlatFieldMapper("http://localhost:8000")
    
    # Configure
    await mapper.configure_collection(
        client_id="my-site",
        collection_name="articles", 
        field_paths=["title", "content"],
        field_types={"title": "text", "content": "wysiwyg"}
    )
    
    # Extract fields
    content = {
        "id": 1,
        "title": "Article Title",
        "content": "<p>HTML content</p>"
    }
    
    result = await mapper.extract_translatable_fields(
        "my-site", "articles", content
    )
    print(result)

asyncio.run(main())
```

### Directus Webhook Integration
```javascript
// Directus webhook handler
export default async function handler(req, res) {
    const { collection, keys, payload } = req.body;
    
    // Configure LocPlat field mapping
    const fieldConfig = {
        client_id: process.env.DIRECTUS_PROJECT_ID,
        collection_name: collection,
        field_paths: getTranslatableFields(collection),
        directus_translation_pattern: "collection_translations"
    };
    
    // Extract fields for translation
    const extractResponse = await fetch(`${LOCPLAT_URL}/api/v1/field-mapping/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            client_id: process.env.DIRECTUS_PROJECT_ID,
            collection_name: collection,
            content: payload,
            language: 'ar' // Target language
        })
    });
    
    const extracted = await extractResponse.json();
    
    // Send to translation service
    // ... translation logic
    
    res.json({ success: true });
}
```

## Error Handling

### Validation Endpoint
```bash
curl -X POST "http://localhost:8000/api/v1/field-mapping/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "content": {"title": "Test", "content": "Content"},
    "field_paths": ["title", "content", "nonexistent.field"]
  }'

# Response:
{
  "field_paths": {
    "title": {"exists": true, "value_type": "str", "detected_field_type": "text"},
    "content": {"exists": true, "value_type": "str", "detected_field_type": "text"}, 
    "nonexistent.field": {"exists": false, "value_type": null, "detected_field_type": null}
  },
  "total_valid": 2,
  "total_tested": 3
}
```

## Performance Considerations

### Caching
- Field configurations are cached for 5 minutes
- Use batch processing for multiple text fields
- HTML parsing is optimized for common structures

### Best Practices
1. **Group similar field types** for batch processing
2. **Use specific field types** instead of auto-detection
3. **Configure RTL mappings** for Arabic content
4. **Validate field paths** before production use
5. **Monitor processing logs** for performance issues
