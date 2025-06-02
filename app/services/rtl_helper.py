"""
Enhanced RTL Support for LocPlat Translation API
Add this to app/services/rtl_helper.py
"""

class RTLDisplayHelper:
    """Helper class for RTL text display enhancement."""
    
    @staticmethod
    def add_rtl_markers(text: str) -> str:
        """Add Unicode RTL override markers for better terminal display."""
        return f"\u202E{text}\u202C"
    
    @staticmethod
    def create_html_rtl(text: str) -> str:
        """Create HTML with proper RTL attributes."""
        return f'<div dir="rtl" style="text-align: right; direction: rtl; unicode-bidi: bidi-override;">{text}</div>'
    
    @staticmethod
    def enhance_translation_response(response: dict) -> dict:
        """Enhance translation response with RTL display options."""
        if response.get("language_direction") == "rtl":
            original_text = response["translated_text"]
            
            # Add display-enhanced versions
            response["display_options"] = {
                "terminal_rtl": RTLDisplayHelper.add_rtl_markers(original_text),
                "html_rtl": RTLDisplayHelper.create_html_rtl(original_text),
                "css_attributes": 'dir="rtl" style="text-align: right; direction: rtl;"'
            }
        
        return response

# Usage example - add this to your translation endpoint
def enhance_api_response_example():
    """Example of how to use RTL helper in your API."""
    
    # Your existing response
    api_response = {
        "translated_text": "مرحبًا بكم في LocPlat!",
        "provider_used": "openai",
        "language_direction": "rtl",
        "quality_score": 0.9
    }
    
    # Enhance for better RTL display
    enhanced_response = RTLDisplayHelper.enhance_translation_response(api_response)
    
    return enhanced_response

if __name__ == "__main__":
    # Test the helper
    example = enhance_api_response_example()
    print("Enhanced API Response:")
    import json
    print(json.dumps(example, indent=2, ensure_ascii=False))
