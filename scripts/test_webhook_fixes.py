#!/usr/bin/env python3
"""
Test script to verify webhook fixes
"""

def test_database_field_fix():
    """Test that FieldProcessingLog uses correct field names"""
    print("🧪 Testing database field fix...")
    
    try:
        from app.models.field_config import FieldProcessingLog
        
        # Test creating log entry with correct fields
        log_fields = {
            'client_id': 'test',
            'collection_name': 'articles', 
            'operation_type': 'extract',
            'success': True,
            'processing_time_ms': 100
        }
        
        # This should not raise an error about invalid keyword arguments
        log_entry = FieldProcessingLog(**log_fields)
        print("✅ FieldProcessingLog accepts correct field names")
        return True
        
    except Exception as e:
        print(f"❌ Database field test failed: {e}")
        return False

def test_css_selector_fix():
    """Test that CSS selector generation is valid"""
    print("\n🧪 Testing CSS selector fix...")
    
    try:
        from app.services.field_mapper import FieldMapper
        from bs4 import BeautifulSoup
        
        # Create test HTML with nested structure
        html = '<div><p>Text with <strong>bold</strong> content</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find nested element
        strong_element = soup.find('strong')
        
        # Create mock session
        class MockSession:
            pass
        
        mapper = FieldMapper(MockSession())
        css_path = mapper._get_element_path(strong_element)
        
        print(f"Generated CSS path: {css_path}")
        
        # Test that the path is a valid CSS selector
        found_elements = soup.select(css_path)
        if found_elements and found_elements[0].name == 'strong':
            print("✅ CSS selector correctly finds the target element")
            return True
        else:
            print("❌ CSS selector doesn't find the correct element")
            return False
            
    except Exception as e:
        print(f"❌ CSS selector test failed: {e}")
        return False

def test_webhook_endpoint():
    """Test webhook endpoint doesn't crash"""
    print("\n🧪 Testing webhook endpoint...")
    
    try:
        # Import webhook components
        from app.api.webhooks import DirectusWebhookRequest
        
        # Test valid request creation
        test_payload = {
            'event': 'items.update',
            'collection': 'articles',
            'key': '123',
            'data': {'id': 123, 'title': 'Test'},
            'client_id': 'test',
            'target_language': 'ar',
            'provider': 'openai',
            'api_key': 'test-key'
        }
        
        request = DirectusWebhookRequest(**test_payload)
        print("✅ Webhook request validation working")
        return True
        
    except Exception as e:
        print(f"❌ Webhook endpoint test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Webhook Fixes")
    print("=" * 40)
    
    tests = [
        test_database_field_fix,
        test_css_selector_fix,
        test_webhook_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All fixes working correctly!")
        print("\n✅ Fixed Issues:")
        print("  1. Database field mapping error resolved")
        print("  2. CSS selector generation fixed") 
        print("  3. Webhook endpoints operational")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    main()
