#!/usr/bin/env python3
"""
Test script to verify HTML translation fix.
"""
import requests
import json
import os

# Test HTML content with text inside tags
test_payload = {
    "event": "items.create",
    "collection": "articles", 
    "key": "1",
    "data": {
        "id": 1,
        "title": "AI Translation Technology",
        "content": "<p>Introduction: AI is transforming <em>multilingual content management</em>. Key benefits include real-time processing.</p>"
    },
    "client_id": "test_html_client",
    "target_language": "ar",
    "provider": "openai",
    "api_key": os.getenv("OPENAI_API_KEY", "test-key-1234567890")
}

def test_html_translation():
    """Test the HTML translation webhook."""
    try:
        print("Testing HTML translation fix...")
        print(f"Original HTML: {test_payload['data']['content']}")
        
        response = requests.post(
            "http://localhost:8000/api/v1/webhooks/directus/translate",
            headers={"Content-Type": "application/json"},
            json=test_payload,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                translated_content = result.get("translated_data", {}).get("translated_content", {})
                translated_html = translated_content.get("content", "")
                
                print(f"Translated HTML: {translated_html}")
                
                # Check if "multilingual content management" was translated
                if "multilingual content management" not in translated_html:
                    print("✅ SUCCESS: HTML text inside tags was translated!")
                    print("✅ The em tag content was properly translated to Arabic")
                else:
                    print("❌ ISSUE: HTML text inside tags was NOT translated")
                    print("❌ 'multilingual content management' is still in English")
                    
                # Show field translations for more detail
                field_translations = result.get("translated_data", {}).get("field_translations", {})
                if "content" in field_translations:
                    content_translation = field_translations["content"]
                    print(f"\nDetailed content translation:")
                    print(f"Provider: {content_translation.get('provider_used')}")
                    print(f"Approach: {content_translation.get('metadata', {}).get('translation_approach')}")
                    print(f"Nodes translated: {content_translation.get('metadata', {}).get('nodes_translated')}")
                    
            else:
                print(f"❌ Translation failed: {result.get('error')}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")

if __name__ == "__main__":
    test_html_translation()
