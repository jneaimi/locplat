"""Enhanced Content Processing Service with Character Handling"""

from typing import Dict, Any
from ..utils.character_handler import character_handler


class EnhancedContentProcessor:
    """Enhanced service for processing structured data with character handling."""
    
    def __init__(self):
        self.supported_providers = ['openai', 'anthropic', 'mistral', 'deepseek']
    
    def preprocess_content(self, content: str, language: str = None) -> Dict[str, Any]:
        """Preprocess content with character validation and repair."""
        if not content:
            return {
                "content": "", 
                "metadata": {
                    "has_special_chars": False, 
                    "preprocessing_applied": False
                }
            }
        
        # Validate and repair character encoding
        validation_result = character_handler.validate_text_encoding(content)
        processed_content = validation_result.repaired_text or content
        
        # Generate character analysis report
        char_report = character_handler.create_character_mapping_report(processed_content)
        
        return {
            "content": processed_content,
            "metadata": {
                "encoding_validation": {
                    "is_valid": validation_result.is_valid,
                    "encoding_issues": validation_result.encoding_issues,
                    "normalization_issues": validation_result.normalization_issues,
                    "warnings": validation_result.warnings
                },
                "character_analysis": char_report,
                "has_special_chars": len(char_report["special_characters_found"]) > 0,
                "preprocessing_applied": validation_result.repaired_text is not None
            }
        }
    
    def _analyze_character_preservation(self, original: str, translation: str) -> Dict[str, Any]:
        """Analyze character preservation quality between original and translation."""
        if not original:
            return {"status": "no_original", "details": "No original text for comparison"}
        
        original_chars = character_handler.find_special_characters(original)
        translation_chars = character_handler.find_special_characters(translation)
        
        missing_chars = original_chars - translation_chars
        extra_chars = translation_chars - original_chars
        
        return {
            "status": "good" if not missing_chars else "warning",
            "original_special_chars": list(original_chars),
            "translation_special_chars": list(translation_chars),
            "missing_chars": list(missing_chars),
            "extra_chars": list(extra_chars),
            "preservation_score": len(original_chars & translation_chars) / len(original_chars) if original_chars else 1.0
        }


__all__ = ['EnhancedContentProcessor']
