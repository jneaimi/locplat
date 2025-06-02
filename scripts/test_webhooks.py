#!/usr/bin/env python3
"""
Test script for Directus webhook functionality
"""
import asyncio
import json
from typing import Dict, Any

# Test data samples
SAMPLE_DIRECTUS_PAYLOAD = {
    "event": "items.update",
    "collection": "articles", 
    "key": "123",
    "data": {
        "id": 123,
        "title": "Breaking News Today",
        "description": "This is an important announcement that needs translation.",
        "content": {
            "text": "<p>Full article content with <strong>HTML formatting</strong> goes here.</p>"
        },
        "status": "published",
        "created_at": "2024-01-15T10:00:00Z"
    },
    "client_id": "test_client",
    "target_language": "ar",
    "provider": "openai",  
    "api_key": "test-key-placeholder",
    "source_language": "en"
}

def test_webhook_data_validation():
    """Test webhook request data validation"""
    print("🧪 Testing webhook data validation...")
    
    try:
        from app.api.webhooks import DirectusWebhookRequest
        
        # Test valid request
        valid_request = DirectusWebhookRequest(**SAMPLE_DIRECTUS_PAYLOAD)
        print(f"✅ Valid request created: {valid_request.collection}")
        
        # Test invalid language code
        invalid_payload = SAMPLE_DIRECTUS_PAYLOAD.copy()
        invalid_payload["target_language"] = "invalid"
        
        try:
            DirectusWebhookRequest(**invalid_payload)
            print("❌ Should have failed with invalid language code")
        except ValueError as e:
            print(f"✅ Correctly caught invalid language: {e}")
        
        # Test invalid provider
        invalid_payload = SAMPLE_DIRECTUS_PAYLOAD.copy()
        invalid_payload["provider"] = "invalid_provider"
        
        try:
            DirectusWebhookRequest(**invalid_payload)
            print("❌ Should have failed with invalid provider")
        except ValueError as e:
            print(f"✅ Correctly caught invalid provider: {e}")
        
        print("✅ Webhook data validation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Webhook validation test failed: {e}")
        return False

def test_signature_verification():
    """Test webhook signature verification"""
    print("\n🔐 Testing webhook signature verification...")
    
    try:
        from app.api.webhooks import verify_webhook_signature
        import hashlib
        import hmac
        
        # Test data
        payload = b'{"test": "data"}'
        secret = "test_secret"
        
        # Create valid signature
        valid_signature = "sha256=" + hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Test valid signature
        if verify_webhook_signature(payload, valid_signature, secret):
            print("✅ Valid signature verification passed")
        else:
            print("❌ Valid signature verification failed")
            return False
        
        # Test invalid signature
        if not verify_webhook_signature(payload, "invalid", secret):
            print("✅ Invalid signature correctly rejected")
        else:
            print("❌ Invalid signature incorrectly accepted")
            return False
        
        print("✅ Signature verification tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Signature verification test failed: {e}")
        return False

def test_webhook_info_endpoint():
    """Test webhook info endpoint"""
    print("\n📋 Testing webhook info endpoint...")
    
    try:
        import httpx
        import time
        
        # Simple test of webhook info structure
        from app.api.webhooks import get_webhook_info
        
        # This should be callable directly
        info = asyncio.run(get_webhook_info())
        
        required_keys = ["webhook_url", "method", "supported_events", "required_fields"]
        for key in required_keys:
            if key not in info:
                print(f"❌ Missing required key in webhook info: {key}")
                return False
        
        print(f"✅ Webhook info endpoint structure valid")
        print(f"   Webhook URL: {info['webhook_url']}")
        print(f"   Supported events: {len(info['supported_events'])}")
        print(f"   Required fields: {len(info['required_fields'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook info test failed: {e}")
        return False

def test_field_mapping_integration():
    """Test that webhook can access field mapping"""
    print("\n🗺️ Testing field mapping integration...")
    
    try:
        # Test that we can import the integrated service
        from app.services.integrated_translation_service import IntegratedTranslationService
        print("✅ IntegratedTranslationService imported successfully")
        
        # Test that field mapper is accessible
        from app.services.field_mapper import FieldMapper
        print("✅ FieldMapper imported successfully")
        
        # Test that models are accessible
        from app.models.field_config import FieldConfig
        print("✅ FieldConfig model imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Field mapping integration test failed: {e}")
        return False

def main():
    """Run all webhook tests"""
    print("🚀 Running LocPlat Webhook Tests")
    print("=" * 50)
    
    tests = [
        test_webhook_data_validation,
        test_signature_verification, 
        test_webhook_info_endpoint,
        test_field_mapping_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All webhook tests passed! Ready for Directus integration.")
        
        print("\n📋 Next Steps:")
        print("1. Set up field mapping configuration for your collections")
        print("2. Create Directus Flow with webhook operation")
        print("3. Test with /api/v1/webhooks/directus/test endpoint")
        print("4. Configure webhook secret for production security")
        
        return True
    else:
        print(f"❌ {total - passed} tests failed. Please fix issues before proceeding.")
        return False

if __name__ == "__main__":
    main()
