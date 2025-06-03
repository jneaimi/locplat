#!/usr/bin/env python3
"""
Setup field configuration for HTML translation test.
"""
import requests
import json

def setup_field_config():
    """Setup field configuration for HTML translation test."""
    config_payload = {
        "client_id": "test_html_client",
        "collection_name": "articles",
        "field_paths": ["title", "content"],
        "field_types": {
            "title": "text",
            "content": "wysiwyg"
        },
        "directus_translation_pattern": "collection_translations",
        "batch_processing": False
    }
    
    try:
        print("Setting up field configuration...")
        response = requests.post(
            "http://localhost:8000/api/v1/field-mapping/config",
            headers={"Content-Type": "application/json"},
            json=config_payload,
            timeout=10
        )
        
        print(f"Field config response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Field configuration created successfully!")
            return True
        else:
            print(f"❌ Failed to create field config: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up field config: {str(e)}")
        return False

if __name__ == "__main__":
    setup_field_config()
