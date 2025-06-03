#!/usr/bin/env python3
"""
Setup common field configurations for testing.
"""
import requests
import json

# Common field configurations for testing
FIELD_CONFIGS = [
    {
        "client_id": "test-directus-client",
        "collection_name": "articles",
        "field_paths": ["title", "content", "description"],
        "field_types": {
            "title": "text",
            "content": "wysiwyg", 
            "description": "textarea"
        },
        "directus_translation_pattern": "collection_translations",
        "batch_processing": False
    },
    {
        "client_id": "test-directus-client", 
        "collection_name": "products",
        "field_paths": ["name", "description", "features"],
        "field_types": {
            "name": "text",
            "description": "textarea",
            "features": "wysiwyg"
        },
        "directus_translation_pattern": "collection_translations",
        "batch_processing": True
    },
    {
        "client_id": "test-html-client",
        "collection_name": "articles", 
        "field_paths": ["title", "content"],
        "field_types": {
            "title": "text",
            "content": "wysiwyg"
        },
        "directus_translation_pattern": "collection_translations",
        "batch_processing": False
    }
]

def setup_field_configs():
    """Setup field configurations for common test scenarios."""
    print("Setting up field configurations for testing...")
    
    for config in FIELD_CONFIGS:
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/field-mapping/config",
                headers={"Content-Type": "application/json"},
                json=config,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Created config for {config['client_id']}/{config['collection_name']} (ID: {result['id']})")
            else:
                print(f"❌ Failed to create config for {config['client_id']}/{config['collection_name']}: {response.text}")
                
        except Exception as e:
            print(f"❌ Error creating config for {config['client_id']}/{config['collection_name']}: {str(e)}")

if __name__ == "__main__":
    setup_field_configs()
    print("\n🎉 Field configuration setup complete!")
    print("\nNow you can test with these client/collection combinations:")
    for config in FIELD_CONFIGS:
        print(f"- {config['client_id']}/{config['collection_name']}")
