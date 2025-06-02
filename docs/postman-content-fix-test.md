# Content Translation Fix Verification Test

## Postman Test Request

**Name**: Verify Content Translation Fixes
**Method**: POST  
**URL**: `{{base_url}}/api/v1/webhooks/directus/test`

### Request Body:
```json
{
  "sample_data": {
    "id": 999,
    "title": "Content Translation Test",
    "content": "<p>This <strong>HTML content</strong> should be fully translated while preserving <em>structure</em>.</p>",
    "summary": "Testing HTML content translation with nested elements"
  },
  "client_id": "test-directus-client",
  "collection": "articles",
  "target_language": "bs",
  "provider": "openai", 
  "api_key": "{{openai_api_key}}",
  "dry_run": false
}
```

### Expected Response Validation:
```javascript
pm.test('Content translation fixes working', function () {
    pm.response.to.have.status(200);
    const responseJson = pm.response.json();
    
    // Verify success
    pm.expect(responseJson.success).to.be.true;
    pm.expect(responseJson.operation).to.equal('translate');
    
    const translatedContent = responseJson.data.translated_content;
    
    // Test Fix 1: Collection ID should be 'articles_id' not 'None_id'
    pm.expect(translatedContent).to.have.property('articles_id');
    pm.expect(translatedContent.articles_id).to.equal(999);
    pm.expect(translatedContent).to.not.have.property('None_id');
    
    // Test Fix 2: HTML content should be translated (not original English)
    const contentField = translatedContent.content;
    pm.expect(contentField).to.be.a('string');
    pm.expect(contentField).to.include('<p>');  // HTML structure preserved
    pm.expect(contentField).to.include('<strong>');  // HTML structure preserved
    pm.expect(contentField).to.include('<em>');  // HTML structure preserved
    pm.expect(contentField).to.not.include('This HTML content should');  // Original English replaced
    
    // Verify language code
    pm.expect(translatedContent.languages_code).to.equal('bs');
    
    console.log('✅ Collection ID Fix: articles_id =', translatedContent.articles_id);
    console.log('✅ HTML Content Translated:', contentField);
});
```

## Expected Fixed Response:
```json
{
  "success": true,
  "operation": "translate",
  "data": {
    "translated_content": {
      "id": null,
      "articles_id": 999,  // ✅ Fixed: Previously was "None_id"
      "languages_code": "bs",
      "title": "Test prijevoda sadržaja",
      "content": "<p>Ovaj <strong>HTML sadržaj</strong> treba biti potpuno preveden zadržavajući <em>strukturu</em>.</p>",  // ✅ Fixed: Now translated
      "summary": "Testiranje prijevoda HTML sadržaja s ugniježđenim elementima"
    },
    "field_translations": {
      "title": {
        "translated_text": "Test prijevoda sadržaja",
        "provider_used": "openai",
        "source_lang": "en",
        "target_lang": "bs"
      },
      "content": {
        "translated_text": "<p>Ovaj <strong>HTML sadržaj</strong> treba biti potpuno preveden zadržavajući <em>strukturu</em>.</p>",
        "provider_used": "openai",
        "source_lang": "en", 
        "target_lang": "bs",
        "metadata": {
          "html_preserved": true,
          "text_nodes_translated": 3
        }
      },
      "summary": {
        "translated_text": "Testiranje prijevoda HTML sadržaja s ugniježđenim elementima",
        "provider_used": "openai",
        "source_lang": "en",
        "target_lang": "bs"
      }
    }
  }
}
```

This test specifically validates that both critical issues have been resolved:
1. **Collection ID**: Generates `articles_id` instead of `None_id`
2. **HTML Translation**: Fully translates content while preserving HTML structure
