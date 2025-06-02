#!/usr/bin/env python3
"""
Simple RTL Display Test for Arabic Text
Demonstrates the issue and provides solutions
"""
import json
import sys
import os

def test_arabic_display():
    """Test Arabic text display in different contexts."""
    
    # The Arabic text from your output
    arabic_text = "مرحبًا بكم في LocPlat! يسهل نظام تخطيط الحقول لدينا ترجمة الهياكل المحتوى المعقدة من نظام إدارة المحتوى Directus."
    
    print("🚀 LocPlat RTL Display Analysis")
    print("=" * 50)
    
    # 1. Show the issue - raw display
    print("\n1️⃣ Raw Arabic Text (may appear incorrect in terminal):")
    print(f"   {arabic_text}")
    
    # 2. Character analysis
    print(f"\n2️⃣ Character Analysis:")
    print(f"   Length: {len(arabic_text)} characters")
    print(f"   UTF-8 bytes: {len(arabic_text.encode('utf-8'))} bytes")
    
    # Check for Arabic Unicode range
    arabic_count = sum(1 for c in arabic_text if 0x0600 <= ord(c) <= 0x06FF)
    print(f"   Arabic characters: {arabic_count}")
    print(f"   Contains RTL chars: {arabic_count > 0}")
    
    # 3. JSON representation (your API output format)
    print(f"\n3️⃣ JSON Response Format (like your API):")
    response_data = {
        "translated_text": arabic_text,
        "provider_used": "openai",
        "model_used": "gpt-4o-mini",
        "source_lang": "en",
        "target_lang": "ar",
        "quality_score": 0.9,
        "language_direction": "rtl",
        "metadata": {
            "model_used": "gpt-4o-mini",
            "language_direction": "rtl",
            "context_used": True
        }
    }
    
    # Display JSON with proper Unicode handling
    print(json.dumps(response_data, indent=2, ensure_ascii=False))
    
    # 4. The problem and solutions
    print(f"\n4️⃣ RTL Display Issues & Solutions:")
    print("   PROBLEM: Terminal/interface may show Arabic left-to-right")
    print("   SOLUTIONS:")
    print("   a) Use RTL-aware terminal (iTerm2, Windows Terminal)")
    print("   b) Add Unicode RTL markers")
    print("   c) Use proper HTML/CSS for web display")
    
    # 5. Create test HTML file
    create_html_test(arabic_text)
    
    print(f"\n5️⃣ Unicode Direction Markers Test:")
    
    # Test with RTL override marker
    rtl_marked = f"\u202E{arabic_text}\u202C"  # RTL override + pop directional formatting
    print(f"   With RTL marker: {rtl_marked}")
    
    # Test with Arabic letter mark
    alm_marked = f"\u061C{arabic_text}"  # Arabic Letter Mark
    print(f"   With ALM marker: {alm_marked}")
    
    print(f"\n✅ Test completed! Check 'rtl_test.html' for proper display.")

def create_html_test(arabic_text):
    """Create HTML file for proper RTL testing."""
    html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>LocPlat RTL Test</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; }}
        .rtl {{ direction: rtl; text-align: right; background: #f0f8ff; padding: 15px; margin: 10px 0; }}
        .ltr {{ direction: ltr; text-align: left; background: #fff0f0; padding: 15px; margin: 10px 0; }}
        .comparison {{ display: flex; gap: 20px; }}
        .comparison > div {{ flex: 1; }}
        h2 {{ color: #333; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>LocPlat RTL Display Test</h1>
    
    <h2>English Original</h2>
    <div class="ltr">
        Welcome to LocPlat! Our field mapping system makes it easy to translate complex content structures from Directus CMS.
    </div>
    
    <h2>Arabic Translation (Proper RTL)</h2>
    <div class="rtl">
        {arabic_text}
    </div>
    
    <h2>Comparison</h2>
    <div class="comparison">
        <div>
            <h3>Wrong (LTR forced)</h3>
            <div class="ltr" style="direction: ltr;">
                {arabic_text}
            </div>
        </div>
        <div>
            <h3>Correct (RTL)</h3>
            <div class="rtl">
                {arabic_text}
            </div>
        </div>
    </div>
    
    <h2>JSON API Response</h2>
    <pre>{json.dumps({
        "translated_text": arabic_text,
        "language_direction": "rtl",
        "quality_score": 0.9
    }, indent=2, ensure_ascii=False)}</pre>
    
    <h2>✅ Result</h2>
    <p><strong>If the "Correct (RTL)" version above flows right-to-left, your display is working properly!</strong></p>
    <p>If both versions look the same, you need RTL support in your terminal/interface.</p>
</body>
</html>"""
    
    try:
        with open("/Users/jneaimimacmini/dev/python/locplat/rtl_test.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("   📄 Created: rtl_test.html")
    except Exception as e:
        print(f"   ❌ Failed to create HTML: {e}")

if __name__ == "__main__":
    test_arabic_display()
