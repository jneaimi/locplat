#!/usr/bin/env python3
"""LocPlat Field Mapping Setup and Test Script"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.config import settings
from app.models.field_config import create_tables
from app.database import SessionLocal
from app.services.field_mapper import FieldMapper


async def test_field_mapping_system():
    """Test the field mapping system with sample data."""
    print("🔧 Testing Field Mapping System...")
    
    # Create database session
    db = SessionLocal()
    field_mapper = FieldMapper(db, enable_logging=True)
    
    try:
        # Test 1: Save a field configuration
        print("\n📝 Test 1: Saving field configuration...")
        test_config = {
            "field_paths": ["title", "content", "summary"],
            "field_types": {
                "title": "text",
                "content": "wysiwyg", 
                "summary": "textarea"
            },
            "directus_translation_pattern": "collection_translations",
            "batch_processing": False,
            "preserve_html_structure": True
        }
        
        await field_mapper.save_field_config(
            client_id="test-client",
            collection_name="articles",
            field_config=test_config
        )
        print("✅ Field configuration saved successfully")
        
        # Test 2: Retrieve the configuration
        print("\n📖 Test 2: Retrieving field configuration...")
        retrieved_config = await field_mapper.get_field_config(
            client_id="test-client",
            collection_name="articles"
        )
        print(f"✅ Retrieved config with {len(retrieved_config['field_paths'])} field paths")
        
        # Test 3: Extract fields from sample content
        print("\n🔍 Test 3: Extracting fields from sample content...")
        sample_content = {
            "id": 1,
            "title": "Sample Article Title",
            "content": "<p>This is <strong>rich text</strong> content with <a href='#'>links</a></p>",
            "summary": "This is a brief summary\nwith multiple lines",
            "author": "John Doe",  # This should be ignored (not in field_paths)
            "metadata": {
                "description": "SEO description"
            }
        }
        
        extracted = field_mapper.extract_fields(
            content=sample_content,
            field_config=retrieved_config
        )
        
        print(f"✅ Extracted {len(extracted)} fields:")
        for path, field_data in extracted.items():
            if path != "__batch__":
                print(f"   - {path}: {field_data['type']} ({len(str(field_data['value']))} chars)")
        
        # Test 4: Test HTML processing
        print("\n🌐 Test 4: Testing HTML content processing...")
        html_content = "<div><h2>Article Header</h2><p>Paragraph with <em>emphasis</em></p></div>"
        
        if field_mapper.is_html(html_content):
            text_nodes = field_mapper.extract_text_from_html(html_content)
            print(f"✅ Extracted {len(text_nodes)} text nodes from HTML")
            for node in text_nodes:
                print(f"   - '{node['text']}' in {node['parent_tag']} tag")
        
        # Test 5: Test nested value extraction
        print("\n🔗 Test 5: Testing nested value extraction...")
        nested_data = {
            "article": {
                "translations": [
                    {"language": "en", "title": "English Title"},
                    {"language": "ar", "title": "Arabic Title"}
                ]
            }
        }
        
        en_title = field_mapper._get_nested_value(nested_data, "article.translations[0].title")
        ar_title = field_mapper._get_nested_value(nested_data, "article.translations[1].title")
        
        print(f"✅ Nested extraction: EN='{en_title}', AR='{ar_title}'")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        db.close()
    
    return True


def main():
    """Main function to set up and test the field mapping system."""
    print("🚀 LocPlat Field Mapping Setup")
    
    # Step 1: Create database tables
    print("\n📦 Creating database tables...")
    try:
        engine = create_engine(settings.DATABASE_URL)
        create_tables(engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return
    
    # Step 2: Run tests
    if asyncio.run(test_field_mapping_system()):
        print("\n✅ Field Mapping System is ready!")
        print("\nNext steps:")
        print("1. Start the server: uvicorn app.main:app --reload")
        print("2. Visit http://localhost:8000/docs to explore the API")
        print("3. Use the field mapping endpoints to configure your collections")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")


if __name__ == "__main__":
    main()
