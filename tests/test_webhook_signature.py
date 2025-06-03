#!/usr/bin/env python3
"""
Test webhook signature generation and verification.
"""
import json
import hmac
import hashlib
import requests

# Webhook secret (must match the one in .env)
WEBHOOK_SECRET = "your-webhook-secret-key-here"

def generate_signature(payload_bytes, secret):
    """Generate SHA-256 signature for webhook payload."""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def test_webhook_signature():
    """Test webhook with proper signature."""
    # Test payload
    payload = {
        "event": "items.create",
        "collection": "articles", 
        "key": "1",
        "data": {
            "id": 1,
            "title": "Test with Signature",
            "content": "This is a test with proper signature"
        },
        "client_id": "test_signature_client",
        "target_language": "ar",
        "provider": "openai",
        "api_key": "test-key-1234567890"
    }
    
    # Convert to JSON bytes
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_bytes = payload_json.encode('utf-8')
    
    # Generate signature
    signature = generate_signature(payload_bytes, WEBHOOK_SECRET)
    
    print(f"Payload: {payload_json}")
    print(f"Signature: {signature}")
    print(f"Secret: {WEBHOOK_SECRET}")
    
    try:
        # Send request with signature
        response = requests.post(
            "http://localhost:8000/api/v1/webhooks/directus/translate",
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature
            },
            data=payload_json,  # Use raw bytes, not json parameter
            timeout=30
        )
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("❌ Signature verification failed")
        elif response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Signature verification passed!")
            else:
                print(f"⚠️ Request authenticated but translation failed: {result.get('error')}")
        else:
            print(f"❓ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request error: {str(e)}")

def test_without_signature():
    """Test webhook without signature (should work if no signature required)."""
    payload = {
        "event": "items.create",
        "collection": "articles", 
        "key": "1",
        "data": {
            "id": 1,
            "title": "Test without Signature",
            "content": "This is a test without signature"
        },
        "client_id": "test_no_signature_client",
        "target_language": "ar",
        "provider": "openai",
        "api_key": "test-key-1234567890"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/webhooks/directus/translate",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        print(f"\n--- Test without signature ---")
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Request without signature accepted (signature not required)")
        else:
            print(f"❌ Request without signature rejected: {response.text}")
            
    except Exception as e:
        print(f"❌ Request error: {str(e)}")

if __name__ == "__main__":
    print("=== Testing Webhook Signature Verification ===")
    test_webhook_signature()
    test_without_signature()
