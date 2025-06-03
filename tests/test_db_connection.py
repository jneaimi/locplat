#!/usr/bin/env python3
"""Test database connection and field mapping functionality"""

import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to Python path
sys.path.insert(0, '/Users/jneaimimacmini/dev/python/locplat')

from app.models.field_config import FieldConfig, FieldProcessingLog
from app.services.field_mapper import FieldMapper


def test_database_connection():
    """Test basic database connection."""
    print("🔍 Testing database connection...")
    
    # Use 127.0.0.1 instead of db for external connection
    DATABASE_URL = "postgresql://locplat:locplat123@127.0.0.1:5432/locplat"
    
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connected successfully!")
            print(f"📊 PostgreSQL version: {version}")
            
            # Test field mapping tables
            result = connection.execute(text("SELECT COUNT(*) FROM field_configs"))
            config_count = result.scalar()
            print(f"📋 Field configs table: {config_count} records")
            
            result = connection.execute(text("SELECT COUNT(*) FROM field_processing_logs"))
            log_count = result.scalar()
            print(f"📝 Processing logs table: {log_count} records")
            
        return True, engine
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False, None

async def test_field_mapper():
    """Test field mapper functionality."""
    print("\n🧪 Testing Field Mapper functionality...")
    
    DATABASE_URL = "postgresql://locplat:locplat123@127.0.0.1:5432/locplat"
    
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        field_mapper = FieldMapper(session, enable_logging=True)
        
        # Test 1: Save a field configuration
        print("📝 Test 1: Saving field configuration...")
        test_config = {
            "field_paths": ["title", "description", "content.text"],
            "field_types": {
                "title": "text",
                "description": "textarea", 
                "content.text": "wysiwyg"
            },
            "is_translation_collection": False,
            "directus_translation_pattern": "collection_translations",
            "batch_processing": True,
            "preserve_html_structure": True,
            "content_sanitization": True
        }
        
        await field_mapper.save_field_config(
            client_id="test_client", 
            collection_name="articles",
            field_config=test_config
        )
        print("✅ Field configuration saved successfully")
        
        # Test 2: Retrieve field configuration
        print("📖 Test 2: Retrieving field configuration...")
        retrieved_config = await field_mapper.get_field_config("test_client", "articles")
        print(f"✅ Retrieved config with {len(retrieved_config['field_paths'])} field paths")        
        # Test 3: Extract fields from sample content
        print("🔍 Test 3: Extracting fields from content...")
        sample_content = {
            "id": 1,
            "title": "Sample Article",
            "description": "This is a sample article description\nwith multiple lines",
            "content": {"text": "<p>This is <strong>HTML content</strong> with markup</p>"},
            "author": "John Doe",
            "published": True
        }
        
        extracted = field_mapper.extract_fields(sample_content, retrieved_config, "ar")
        print(f"✅ Extracted {len([k for k in extracted.keys() if k != '__batch__'])} fields")
        
        for path, data in extracted.items():
            if path != "__batch__":
                value_preview = str(data['value'])[:50]
                if len(str(data['value'])) > 50:
                    value_preview += '...'
                print(f"   📄 {path}: {data['type']} -> '{value_preview}'")
            else:
                batch_count = len(data.get('text', []))
                print(f"   📦 Batch content: {batch_count} items for batch processing")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Field mapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚀 LocPlat Field Mapping Database Test")
    print("=" * 50)
    
    # Test 1: Database connection
    success, engine = test_database_connection()
    if not success:
        sys.exit(1)
    
    # Test 2: Field mapper functionality
    success = await test_field_mapper()
    if not success:
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed successfully!")
    print("\n📋 Summary:")
    print("✅ Database connection working")
    print("✅ Field mapping tables accessible") 
    print("✅ Field configuration save/retrieve working")
    print("✅ Field extraction working")
    print("\n🚀 Ready to proceed with integration!")


if __name__ == "__main__":
    asyncio.run(main())
