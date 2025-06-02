"""Tests for Field Mapping functionality"""

import pytest
import json
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.field_mapper import FieldMapper
from app.models.field_types import FieldType, DirectusTranslationPattern


class TestFieldMapper:
    """Test suite for FieldMapper service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.field_mapper = FieldMapper(self.mock_db, enable_logging=False)
    
    def test_detect_field_type_text(self):
        """Test field type detection for plain text."""
        assert self.field_mapper._detect_field_type("Simple text") == FieldType.TEXT.value
    
    def test_detect_field_type_html(self):
        """Test field type detection for HTML content."""
        html_content = "<p>HTML content</p>"
        assert self.field_mapper._detect_field_type(html_content) == FieldType.WYSIWYG.value
    
    def test_detect_field_type_textarea(self):
        """Test field type detection for multiline text."""
        multiline_text = "Line 1\nLine 2\nLine 3"
        assert self.field_mapper._detect_field_type(multiline_text) == FieldType.TEXTAREA.value
    
    def test_detect_field_type_json(self):
        """Test field type detection for JSON content."""
        json_content = {"key": "value"}
        assert self.field_mapper._detect_field_type(json_content) == FieldType.JSON.value
    
    def test_get_nested_value_simple(self):
        """Test getting simple nested values."""
        data = {"title": "Test Title", "content": "Test Content"}
        assert self.field_mapper._get_nested_value(data, "title") == "Test Title"
        assert self.field_mapper._get_nested_value(data, "content") == "Test Content"
    
    def test_get_nested_value_deep_nesting(self):
        """Test getting deeply nested values."""
        data = {
            "article": {
                "title": "Article Title",
                "author": {
                    "name": "John Doe",
                    "bio": "Author bio"
                }
            }
        }
        assert self.field_mapper._get_nested_value(data, "article.title") == "Article Title"
        assert self.field_mapper._get_nested_value(data, "article.author.name") == "John Doe"
    
    def test_get_nested_value_array_index(self):
        """Test getting values from arrays."""
        data = {
            "tags": ["tag1", "tag2", "tag3"],
            "items": [
                {"name": "Item 1", "value": 100},
                {"name": "Item 2", "value": 200}
            ]
        }
        assert self.field_mapper._get_nested_value(data, "tags[0]") == "tag1"
        assert self.field_mapper._get_nested_value(data, "items[1].name") == "Item 2"
    
    def test_get_nested_value_missing_path(self):
        """Test getting values for non-existent paths."""
        data = {"title": "Test"}
        assert self.field_mapper._get_nested_value(data, "nonexistent") is None
        assert self.field_mapper._get_nested_value(data, "title.sub") is None
    
    def test_is_html_detection(self):
        """Test HTML content detection."""
        assert self.field_mapper.is_html("<p>HTML content</p>") is True
        assert self.field_mapper.is_html("<div><span>Nested</span></div>") is True
        assert self.field_mapper.is_html("Plain text") is False
        assert self.field_mapper.is_html("Text with < symbols but not tags") is False
    
    def test_extract_fields_simple(self):
        """Test basic field extraction."""
        content = {
            "title": "Article Title",
            "content": "Article content",
            "summary": "Brief summary"
        }
        
        field_config = {
            "field_paths": ["title", "content"],
            "field_types": {},
            "batch_processing": False
        }
        
        result = self.field_mapper.extract_fields(content, field_config)
        
        assert "title" in result
        assert "content" in result
        assert result["title"]["value"] == "Article Title"
        assert result["content"]["value"] == "Article content"
        assert "summary" not in result  # Not in field_paths
    
    def test_extract_fields_with_html(self):
        """Test field extraction with HTML content."""
        content = {
            "title": "Article Title",
            "content": "<p>HTML <strong>content</strong></p>"
        }
        
        field_config = {
            "field_paths": ["title", "content"],
            "field_types": {},
            "batch_processing": False
        }
        
        result = self.field_mapper.extract_fields(content, field_config)
        
        assert result["content"]["type"] == FieldType.WYSIWYG.value
        assert "html_structure" in result["content"]["metadata"]


class TestContentProcessor:
    """Test suite for ContentProcessor service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        from app.services.content_processor import ContentProcessor
        self.processor = ContentProcessor()
    
    def test_process_openai_response(self):
        """Test processing OpenAI-style response."""
        structured_data = {
            "choices": [{
                "message": {
                    "content": '{"title": "Translated Title", "content": "Translated Content"}'
                }
            }]
        }
        
        field_config = {
            "field_paths": ["title", "content"],
            "field_types": {"title": FieldType.TEXT.value, "content": FieldType.WYSIWYG.value}
        }
        
        result = self.processor.process_ai_structured_data(structured_data, field_config)
        
        assert "title" in result
        assert "content" in result
        assert result["title"]["value"] == "Translated Title"
        assert result["content"]["value"] == "Translated Content"


# Integration test example
@pytest.mark.asyncio
async def test_field_config_integration():
    """Test field configuration save and retrieve."""
    # This would require a test database setup
    # Implementation depends on your testing framework setup
    pass


if __name__ == "__main__":
    pytest.main([__file__])
