"""Content Processing Service for AI Provider Integration"""

import json
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from ..models.field_types import FieldType


class ContentProcessor:
    """Service for processing structured data from AI providers."""
    
    def __init__(self):
        self.supported_providers = ['openai', 'anthropic', 'mistral', 'deepseek']
    
    def process_ai_structured_data(self, structured_data: Dict[str, Any], 
                                  field_config: Dict[str, Any], 
                                  provider: str = None) -> Dict[str, Any]:
        """Process structured data from AI providers."""
        result = {}
        
        # Handle different AI provider response formats
        if "translations" in structured_data:
            # Standard translation response format
            translations = structured_data.get("translations", [])
            for i, translation in enumerate(translations):
                if i < len(field_config.get("field_paths", [])):
                    path = field_config["field_paths"][i]
                    result[path] = {
                        "value": translation.get("text", ""),
                        "type": field_config.get("field_types", {}).get(path, FieldType.TEXT.value),
                        "metadata": {
                            "detected_language": translation.get("detected_language"),
                            "target_language": translation.get("to"),
                            "confidence": translation.get("confidence", 1.0)
                        }
                    }
        
        elif "choices" in structured_data:
            # OpenAI-style response format
            choices = structured_data.get("choices", [])
            if choices and "message" in choices[0]:
                content = choices[0].get("message", {}).get("content", "")
                result = self._parse_content_response(content, field_config)
        
        elif "content" in structured_data:
            # Direct content response (Anthropic style)
            content = structured_data.get("content", "")
            if isinstance(content, list) and content:
                content = content[0].get("text", "") if isinstance(content[0], dict) else str(content[0])
            result = self._parse_content_response(content, field_config)
        
        elif "response" in structured_data:
            # Generic response format
            content = structured_data.get("response", "")
            result = self._parse_content_response(content, field_config)
        
        return result
    
    def _parse_content_response(self, content: str, field_config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse content response from AI providers."""
        result = {}
        
        # Try to parse as JSON first
        if content.strip().startswith("{") and content.strip().endswith("}"):
            try:
                parsed = json.loads(content)
                for path in field_config.get("field_paths", []):
                    if path in parsed:
                        result[path] = {
                            "value": parsed[path],
                            "type": field_config.get("field_types", {}).get(path, FieldType.TEXT.value),
                            "metadata": {}
                        }
                return result
            except json.JSONDecodeError:
                pass
        
        # Try to parse as structured text with field markers
        field_patterns = [
            r'(?:^|\n)(?:Field|Path):\s*([^\n]+)\n(?:Value|Translation):\s*([^\n]+)',
            r'(?:^|\n)([^:]+):\s*([^\n]+)',
            r'(?:^|\n)(?:##?\s*)?([^#\n]+)(?:\n|$)([^#\n]+)'
        ]
        
        for pattern in field_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            if matches:
                field_paths = field_config.get("field_paths", [])
                for i, (field, value) in enumerate(matches):
                    if i < len(field_paths):
                        path = field_paths[i]
                        result[path] = {
                            "value": value.strip(),
                            "type": field_config.get("field_types", {}).get(path, FieldType.TEXT.value),
                            "metadata": {}
                        }
                break
        
        # Fallback: treat entire content as single field translation
        if not result and field_config.get("field_paths"):
            result[field_config["field_paths"][0]] = {
                "value": content.strip(),
                "type": FieldType.TEXT.value,
                "metadata": {}
            }
        
        return result


__all__ = ['ContentProcessor']
