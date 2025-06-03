"""
Tests for enhanced content processor with character handling.
"""
import pytest
from app.services.enhanced_content_processor import EnhancedContentProcessor


class TestEnhancedContentProcessor:
    """Test suite for EnhancedContentProcessor."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.processor = EnhancedContentProcessor()
    
    def test_preprocess_content_basic(self):
        """Test basic content preprocessing."""
        content = "Tekst sa specijalnim znakovima: čšđćž"
        result = self.processor.preprocess_content(content, 'bs')
        
        assert result['content'] == content  # Should remain unchanged if valid
        assert 'metadata' in result
        assert 'encoding_validation' in result['metadata']
        assert 'character_analysis' in result['metadata']
        assert result['metadata']['has_special_chars'] == True
    
    def test_preprocess_content_with_issues(self):
        """Test preprocessing content with encoding issues."""
        # Simulate content with encoding issues
        content = "Problem sa enkodiranjem: Ä\x8d"  # Should be č
        result = self.processor.preprocess_content(content, 'bs')
        
        # Should repair the issue
        assert result['content'] != content
        assert 'č' in result['content']
        assert result['metadata']['preprocessing_applied'] == True
    
    def test_character_preservation_analysis(self):
        """Test character preservation analysis."""
        original = "Čovek čuva školu u gradu."
        translation_good = "Man guards school in city."  # No special chars expected
        translation_bad = "Covek cuva skolu u gradu."   # Lost special chars
        
        # Good translation (no special chars expected in English)
        analysis_good = self.processor._analyze_character_preservation(original, translation_good)
        assert analysis_good['status'] in ['good', 'warning']
        
        # Bad translation (special chars lost in same language)
        analysis_bad = self.processor._analyze_character_preservation(original, translation_bad)
        assert len(analysis_bad['missing_chars']) > 0
        assert analysis_bad['preservation_score'] < 1.0
    
    def test_empty_content_handling(self):
        """Test handling of empty or invalid content."""
        # Empty content
        result_empty = self.processor.preprocess_content("", "bs")
        assert result_empty['content'] == ""
        assert not result_empty['metadata']['has_special_chars']
        
        # None content should be handled gracefully
        result_none = self.processor.preprocess_content(None, "bs")
        assert result_none['content'] == ""


if __name__ == "__main__":
    pytest.main([__file__])
    
    def test_ai_structured_data_processing(self):
        """Test processing of AI provider structured data."""
        # Simulate OpenAI-style response
        structured_data = {
            "choices": [{
                "message": {
                    "content": '{"title": "Čuvar škole", "description": "Đorđe čuva školu u gradu."}'
                }
            }]
        }
        
        field_config = {
            "field_paths": ["title", "description"],
            "field_types": {"title": FieldType.TEXT.value, "description": FieldType.TEXT.value},
            "original_texts": ["School Guardian", "George guards school in city."]
        }
        
        result = self.processor.process_ai_structured_data(
            structured_data, field_config, "openai", "en", "bs"
        )
        
        assert "title" in result
        assert "description" in result
        assert "Čuvar" in result["title"]["value"]
        assert "metadata" in result["title"]
    
    def test_content_response_parsing(self):
        """Test parsing of content responses with character handling."""
        content = "Title: Čuvar škole\nDescription: Đorđe čuva školu."
        field_config = {
            "field_paths": ["title", "description"],
            "original_texts": ["School Guardian", "George guards school."]
        }
        
        result = self.processor._parse_content_response(
            content, field_config, "en", "bs"
        )
        
        assert len(result) == 2
        assert "title" in result
        assert "description" in result
        # Should preserve special characters
        assert "č" in result["title"]["value"]
    
    def test_post_processing_translation(self):
        """Test post-processing of translations."""
        original = "Čovek čuva školu."
        translation = "Covek cuva skolu."  # Missing special chars
        
        processed = self.processor._post_process_translation(
            original, translation, "bs", "bs"
        )
        
        # Should be normalized at minimum
        assert len(processed) >= len(translation)
        
    def test_empty_content_handling(self):
        """Test handling of empty or invalid content."""
        # Empty content
        result_empty = self.processor.preprocess_content("", "bs")
        assert result_empty['content'] == ""
        assert not result_empty['metadata']['has_special_chars']
        
        # None content should be handled gracefully
        result_none = self.processor.preprocess_content(None, "bs")
        assert result_none['content'] == ""


if __name__ == "__main__":
    pytest.main([__file__])
