"""
RTL Display Fix for LocPlat API Responses
Add this to your translation service to improve RTL display
"""

def enhance_rtl_display(text: str, language_direction: str) -> str:
    """Add Unicode RTL markers for better terminal display."""
    if language_direction == "rtl":
        # Add RTL override marker at start and pop at end
        return f"\u202E{text}\u202C"
    return text

def format_api_response_for_display(response_data: dict) -> dict:
    """Format API response with better RTL display."""
    if response_data.get("language_direction") == "rtl":
        # Add display-enhanced version
        response_data["translated_text_display"] = enhance_rtl_display(
            response_data["translated_text"], 
            response_data["language_direction"]
        )
        
        # Add HTML-ready version
        response_data["translated_text_html"] = (
            f'<div dir="rtl" style="text-align: right; direction: rtl;">'
            f'{response_data["translated_text"]}</div>'
        )
    
    return response_data

# Example usage:
example_response = {
    "translated_text": "مرحبًا بكم في LocPlat! يسهل نظام تخطيط الحقول لدينا ترجمة الهياكل المحتوى المعقدة من نظام إدارة المحتوى Directus.",
    "provider_used": "openai",
    "model_used": "gpt-4o-mini",
    "source_lang": "en",
    "target_lang": "ar",
    "quality_score": 0.9,
    "language_direction": "rtl"
}

# Enhanced response for better display
enhanced = format_api_response_for_display(example_response)
print("Enhanced RTL Response:")
print(f"Display version: {enhanced.get('translated_text_display', '')}")
print(f"HTML version: {enhanced.get('translated_text_html', '')}")
