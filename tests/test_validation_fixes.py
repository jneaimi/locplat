#!/usr/bin/env python3
"""
Quick test to identify the specific validation issues
"""

import asyncio
import json
import aiohttp

async def test_webhook_validation():
    """Test the webhook validation endpoint with proper data"""
    url = "http://localhost:8000/api/v1/webhooks/directus/validate"
    
    # Test data that should be valid
    test_data = {
        "client_id": "test_client",
        "collection": "articles", 
        "provider": "openai",
        "api_key": "sk-test12345678901234567890123456789012345678901234567890",
        "target_language": "ar"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_data) as response:
                status = response.status
                text = await response.text()
                
                print(f"Status: {status}")
                print(f"Response: {text}")
                
                if status == 422:
                    print("\n422 Validation Error Details:")
                    try:
                        error_data = json.loads(text)
                        if 'detail' in error_data:
                            if isinstance(error_data['detail'], list):
                                for error in error_data['detail']:
                                    print(f"  Field: {error.get('loc', 'unknown')}")
                                    print(f"  Message: {error.get('msg', 'unknown')}")
                                    print(f"  Type: {error.get('type', 'unknown')}")
                                    print("  ---")
                            else:
                                print(f"  Message: {error_data['detail']}")
                    except json.JSONDecodeError:
                        print(f"  Raw error: {text}")
                
                return status == 200
                
    except Exception as e:
        print(f"Connection error: {e}")
        return False

async def test_field_config():
    """Test field configuration endpoint"""
    url = "http://localhost:8000/api/v1/field-mapping/config"
    
    test_data = {
        "client_id": "test_client",
        "collection_name": "articles",
        "field_paths": ["title", "description"],
        "field_types": {"title": "text", "description": "textarea"},
        "batch_processing": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_data) as response:
                status = response.status
                text = await response.text()
                
                print(f"\nField Config - Status: {status}")
                print(f"Response: {text}")
                
                if status == 500:
                    print("\n500 Server Error - likely database issue")
                
                return status == 200
                
    except Exception as e:
        print(f"Connection error: {e}")
        return False

async def main():
    """Run validation tests"""
    print("Testing LocPlat validation issues...")
    print("=" * 40)
    
    webhook_ok = await test_webhook_validation()
    field_config_ok = await test_field_config()
    
    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"Webhook validation: {'✅ FIXED' if webhook_ok else '❌ STILL BROKEN'}")
    print(f"Field configuration: {'✅ FIXED' if field_config_ok else '❌ STILL BROKEN'}")

if __name__ == "__main__":
    asyncio.run(main())
