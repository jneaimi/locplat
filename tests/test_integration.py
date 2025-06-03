#!/usr/bin/env python3
"""
Test script for Integrated Translation Service
"""
import asyncio
import json
import sys
import os

# Add the app directory to the path
sys.path.append('/Users/jneaimimacmini/dev/python/locplat')

from app.database import get_db
from app.services.integrated_translation_service import IntegratedTranslationService


async def test_integrated_translation():
    """Test the integrated translation service."""
    print("🧪 Testing Integrated Translation Service...")
    
    # Get database session
    db = next(get_db())
    
    # Initialize service
    service = IntegratedTranslationService(db)
    
    # Test content
    test_content = {
        "id": 1,
        "title": "Welcome to our website",
        "description": "This is a sample description for testing.",
        "content": {
            "text": "<p>Hello <strong>world</strong>! This is HTML content.</p>"
        },
        "author": "Test Author",
        "status": "published"
    }
    
    print(f"📄 Test content: {json.dumps(test_content, indent=2)}")
    
    # Test 1: Preview what would be translated
    print("\n1️⃣ Testing translation preview...")
    try:
        preview = await service.get_translation_preview(
            content=test_content,
            client_id="test_client", 
            collection_name="articles",
            target_lang="ar"
        )
        print(f"✅ Preview result: {json.dumps(preview, indent=2)}")
    except Exception as e:
        print(f"❌ Preview failed: {str(e)}")
    
    # Test 2: Validate translation request
    print("\n2️⃣ Testing validation...")
    try:
        validation = await service.validate_translation_request(
            client_id="test_client",
            collection_name="articles", 
            provider="openai",
            api_key="sk-test-key-1234567890",  # Fake key for testing
            source_lang="en",
            target_lang="ar"
        )
        print(f"✅ Validation result: {json.dumps(validation, indent=2)}")
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
    
    # Test 3: Check field configuration
    print("\n3️⃣ Testing field configuration retrieval...")
    try:
        config = await service.field_mapper.get_field_config("test_client", "articles")
        print(f"✅ Field config: {json.dumps(config, indent=2)}")
    except Exception as e:
        print(f"❌ Config retrieval failed: {str(e)}")
    
    print("\n🎉 Integration test completed!")


if __name__ == "__main__":
    asyncio.run(test_integrated_translation())
