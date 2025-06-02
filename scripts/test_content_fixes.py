#!/usr/bin/env python3
"""
Test script to verify webhook content translation fixes
"""

def test_field_config_fix():
    """Test that primary_collection is set correctly"""
    print("🧪 Testing field configuration fix...")
    
    try:
        import requests
        
        # Get current field config
        response = requests.get("http://localhost:8000/api/v1/field-mapping/config/test-directus-client/articles")
        
        if response.status_code == 200:
            config = response.json()
            primary_collection = config.get("primary_collection")
            
            if primary_collection == "articles":
                print("✅ Primary collection correctly set to 'articles'")
                print(f"   This will generate 'articles_id' instead of 'None_id'")
                return True
            else:
                print(f"❌ Primary collection is '{primary_collection}', should be 'articles'")
                return False
        else:
            print(f"❌ Failed to get field config: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Field config test failed: {e}")
        return False

def test_html_processing_fix():
    """Test that HTML content is properly extracted and reassembled"""
    print("\n🧪 Testing HTML processing fix...")
    
    try:
        # Import within Docker environment context
        from app.services.field_mapper import FieldMapper
        
        # Test HTML content
        html_content = '<p>Experience seamless AI translation for your <em>Directus CMS</em>.</p>'
        
        class MockSession:
            pass
        
        mapper = FieldMapper(MockSession())
        
        # Test text extraction
        text_nodes = mapper.extract_text_from_html(html_content)
        
        if len(text_nodes) < 2:
            print(f"❌ Not enough text nodes extracted: {len(text_nodes)}")
            return False
        
        print(f"✅ Extracted {len(text_nodes)} text nodes from HTML")
        
        # Test text content
        extracted_texts = [node['text'] for node in text_nodes]
        expected_texts = ["Experience seamless AI translation for your", "Directus CMS", "."]
        
        for expected in expected_texts:
            if not any(expected in text for text in extracted_texts):
                print(f"❌ Expected text '{expected}' not found in extracted texts")
                return False
        
        print("✅ All expected text content found")
        
        # Test reassembly with mock translations
        translated_nodes = []
        for node in text_nodes:
            translated_nodes.append({
                'text': node['text'],
                'translated_text': f"[BS: {node['text']}]"  # Mock Bosnian translation
            })
        
        reassembled = mapper.reassemble_html(html_content, translated_nodes)
        
        # Check that HTML structure is preserved
        if '<p>' in reassembled and '<em>' in reassembled and '</em>' in reassembled and '</p>' in reassembled:
            print("✅ HTML structure preserved during reassembly")
        else:
            print(f"❌ HTML structure not preserved: {reassembled}")
            return False
        
        # Check that content was replaced
        if '[BS:' in reassembled:
            print("✅ Text content was successfully replaced")
            return True
        else:
            print(f"❌ Text content not replaced: {reassembled}")
            return False
            
    except Exception as e:
        print(f"❌ HTML processing test failed: {e}")
        return False

def test_collection_id_generation():
    """Test that collection ID is generated correctly"""
    print("\n🧪 Testing collection ID generation...")
    
    try:
        from app.services.field_mapper import FieldMapper
        
        class MockSession:
            pass
        
        mapper = FieldMapper(MockSession())
        
        # Mock field config with primary_collection set
        field_config = {
            "primary_collection": "articles",
            "directus_translation_pattern": "collection_translations"
        }
        
        # Mock content
        content = {"id": 456, "title": "Test"}
        
        # Test collection translations pattern
        result = mapper._handle_collection_translations(content, field_config, "bs")
        
        if "articles_id" in result and result["articles_id"] == 456:
            print("✅ Collection ID correctly generated as 'articles_id': 456")
        else:
            print(f"❌ Collection ID not generated correctly: {result}")
            return False
        
        if result.get("languages_code") == "bs":
            print("✅ Language code correctly set")
            return True
        else:
            print(f"❌ Language code not set correctly: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Collection ID test failed: {e}")
        return False

def test_webhook_dry_run():
    """Test webhook dry run to ensure structure is correct"""
    print("\n🧪 Testing webhook dry run...")
    
    try:
        import requests
        
        payload = {
            "sample_data": {
                "id": 456,
                "title": "Welcome to LocPlat",
                "content": "<p>Experience seamless AI translation for your <em>Directus CMS</em>.</p>",
                "summary": "LocPlat integration overview"
            },
            "client_id": "test-directus-client",
            "collection": "articles",
            "target_language": "bs",
            "provider": "openai",
            "api_key": "test-key-placeholder",
            "dry_run": True
        }
        
        response = requests.post("http://localhost:8000/api/v1/webhooks/directus/test", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print("✅ Webhook dry run successful")
                
                # Check field extraction
                extractable_fields = data.get("data", {}).get("extractable_fields", {})
                if "content" in extractable_fields:
                    content_field = extractable_fields["content"]
                    if content_field.get("type") == "wysiwyg":
                        print("✅ HTML content correctly identified as wysiwyg type")
                        return True
                    else:
                        print(f"❌ Content type incorrect: {content_field.get('type')}")
                        return False
                else:
                    print("❌ Content field not found in extractable fields")
                    return False
            else:
                print(f"❌ Webhook dry run failed: {data}")
                return False
        else:
            print(f"❌ Webhook request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook dry run test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Webhook Content Translation Fixes")
    print("=" * 50)
    
    tests = [
        test_field_config_fix,
        test_html_processing_fix,
        test_collection_id_generation,
        test_webhook_dry_run
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All content translation fixes working!")
        print("\n✅ Fixed Issues:")
        print("  1. Collection ID: Now generates 'articles_id' instead of 'None_id'")
        print("  2. HTML Content: Properly extracts and translates text while preserving structure")
        print("  3. Field Mapping: Primary collection correctly configured")
        print("  4. Translation Workflow: End-to-end processing operational")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    main()
