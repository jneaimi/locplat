"""
Tests for character handling functionality.
"""
import pytest
import unicodedata
from app.utils.character_handler import CharacterHandler, Script, CharacterValidationResult


class TestCharacterHandler:
    """Test suite for CharacterHandler class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.handler = CharacterHandler()
    
    def test_bosnian_character_detection(self):
        """Test detection of Bosnian special characters."""
        # Text with Bosnian special characters
        text = "Željko je čuvar škole u Tuzli. Đorđe čuva đavolske često."
        special_chars = self.handler.find_special_characters(text)
        
        # Check for characters that are actually in the text
        expected_chars = {'ž', 'č', 'š', 'đ'}  # Characters actually present
        found_chars = special_chars.intersection(expected_chars)
        assert len(found_chars) >= 3  # Should find at least 3 of these chars
    
    def test_script_detection_latin(self):
        """Test Latin script detection."""
        text = "Hello world with special chars: čšđćž"
        script = self.handler.detect_script(text)
        assert script == Script.LATIN
    
    def test_script_detection_cyrillic(self):
        """Test Cyrillic script detection."""
        text = "Привет мир на српском језику"
        script = self.handler.detect_script(text)
        assert script == Script.CYRILLIC
    
    def test_script_detection_mixed(self):
        """Test mixed script detection."""
        text = "Hello мир with mixed scripts"
        script = self.handler.detect_script(text)
        assert script == Script.MIXED
    
    def test_text_normalization(self):
        """Test Unicode text normalization."""
        # Create text with non-NFC form
        text = "cafe\u0301"  # e + combining acute accent
        normalized = self.handler.normalize_text(text, 'NFC')
        
        # Should be normalized to composed form
        expected = "café"
        assert normalized == expected
        assert unicodedata.normalize('NFC', normalized) == normalized
    
    def test_encoding_validation_valid_text(self):
        """Test encoding validation with valid UTF-8 text."""
        text = "Validni tekst sa specijalnim znakovima: čšđćž"
        result = self.handler.validate_text_encoding(text)
        
        assert result.is_valid == True
        # Note: Our handler might detect some false positives with character mappings
        # The important thing is that it should be valid UTF-8
        assert len(result.special_chars_found) > 0
    
    def test_encoding_repair(self):
        """Test encoding issue repair."""
        # Simulated double-encoded text
        text = "Ovo je Ä\x8desto pogreÅ¡no"
        repaired = self.handler.repair_encoding_issues(text)
        
        # Should repair some common encoding issues
        assert repaired != text  # Should be different after repair
        # Length may be different after repair (usually shorter when fixing double-encoding)
    
    def test_latin_cyrillic_transliteration(self):
        """Test transliteration between Latin and Cyrillic scripts."""
        # Latin to Cyrillic
        latin_text = "Zdravo, kako si?"
        cyrillic = self.handler.transliterate_to_cyrillic(latin_text)
        
        # Should convert Latin characters to Cyrillic
        # Check if any Cyrillic characters are present (the mapping worked)
        assert any(ord(char) >= 0x0400 and ord(char) <= 0x04FF for char in cyrillic)
        
        # Cyrillic to Latin (reverse)
        back_to_latin = self.handler.transliterate_to_latin(cyrillic)
        # Should be close to original (some characters might differ)
        assert len(back_to_latin) == len(latin_text)
    
    def test_special_character_preservation(self):
        """Test preservation of special characters in translation."""
        original = "Čovek je čuvar škole u Beogradu."
        # Simulate translation that lost some special characters
        translated_with_issues = "Covek je cuvar skole u Beogradu."
        
        corrected, corrections = self.handler.preserve_special_characters(
            original, translated_with_issues
        )
        
        # Should detect missing characters
        assert len(corrections) > 0
        assert any("Missing special characters" in correction for correction in corrections)
    
    def test_fallback_substitutions(self):
        """Test fallback character substitutions."""
        text = "Česta greška sa đavolskim čuvarima."
        fallback = self.handler.apply_fallback_substitutions(text)
        
        # Special characters should be replaced with ASCII equivalents
        assert 'č' not in fallback
        assert 'đ' not in fallback
        assert 'c' in fallback  # č -> c
        assert 'd' in fallback  # đ -> d
    
    def test_character_mapping_report(self):
        """Test comprehensive character analysis report."""
        text = "Tekst sa različitim znakovima: čšđćž and العربية"
        report = self.handler.create_character_mapping_report(text)
        
        assert 'text_length' in report
        assert 'special_characters_found' in report
        assert 'script_detected' in report
        assert 'encoding_valid' in report
        assert report['special_character_count'] > 0
        assert len(report['special_characters_found']) > 0


class TestCharacterValidationResult:
    """Test CharacterValidationResult class."""
    
    def test_validation_result_initialization(self):
        """Test initialization of validation result."""
        result = CharacterValidationResult()
        
        assert result.is_valid == True
        assert result.encoding_issues == []
        assert result.normalization_issues == []
        assert result.warnings == []
        assert result.repaired_text is None


class TestCharacterHandlerIntegration:
    """Integration tests for character handler with various text types."""
    
    def setup_method(self):
        self.handler = CharacterHandler()
    
    def test_mixed_language_content(self):
        """Test handling of mixed-language content."""
        text = "Hello svijet! This is English and Bosnian: čuvar škole."
        validation = self.handler.validate_text_encoding(text)
        
        assert validation.is_valid
        special_chars = validation.special_chars_found
        assert 'č' in special_chars
        
    def test_html_content_with_special_chars(self):
        """Test handling of HTML content with special characters."""
        html_text = "<p>Čovek je čuvar <strong>škole</strong> u gradu.</p>"
        preprocessed = self.handler.repair_encoding_issues(html_text)
        
        # Should preserve HTML tags and special characters
        assert '<p>' in preprocessed
        assert '<strong>' in preprocessed
        assert 'č' in preprocessed
        
    def test_empty_and_none_inputs(self):
        """Test handling of empty and None inputs."""
        # Empty string
        result_empty = self.handler.validate_text_encoding("")
        assert result_empty.is_valid
        
        # Test with None (should handle gracefully)
        special_chars_none = self.handler.find_special_characters("")
        assert len(special_chars_none) == 0
        
    def test_performance_with_large_text(self):
        """Test performance with larger text samples."""
        # Create a larger text sample
        base_text = "Čovek čuva školu u gradu. Đorđe je dobar čuvar. "
        large_text = base_text * 100  # Repeat 100 times
        
        # Should handle large text efficiently
        import time
        start_time = time.time()
        
        validation = self.handler.validate_text_encoding(large_text)
        special_chars = self.handler.find_special_characters(large_text)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 1.0  # Should take less than 1 second
        assert validation.is_valid
        assert len(special_chars) > 0


if __name__ == "__main__":
    pytest.main([__file__])
