#!/usr/bin/env python3
"""
RTL Display Test for LocPlat
Tests Arabic RTL text display and validation
"""
import asyncio
import json
import sys
import os
import locale
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table


class RTLDisplayTester:
    def __init__(self):
        self.console = Console()
        self.base_url = "http://localhost:8000"
        
    def check_system_rtl_support(self):
        """Check if system supports RTL display."""
        try:
            # Check locale support
            current_locale = locale.getlocale()
            self.console.print(f"📍 Current locale: {current_locale}")
            
            # Check console capabilities
            console_supports_unicode = self.console.options.unicode
            self.console.print(f"🔤 Unicode support: {console_supports_unicode}")
            
            return console_supports_unicode
        except Exception as e:
            self.console.print(f"❌ Error checking system support: {e}")
            return False
    
    def display_arabic_text_analysis(self, arabic_text: str):
        """Analyze and display Arabic text properties."""
        table = Table(title="Arabic Text Analysis")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        # Character analysis
        table.add_row("Original Text", arabic_text)
        table.add_row("Character Count", str(len(arabic_text)))
        table.add_row("Byte Length (UTF-8)", str(len(arabic_text.encode('utf-8'))))
        
        # Unicode analysis
        unicode_points = [f"U+{ord(c):04X}" for c in arabic_text[:10]]  # First 10 chars
        table.add_row("Unicode Points (first 10)", " ".join(unicode_points))
        
        # Check for Arabic Unicode blocks
        arabic_ranges = {
            (0x0600, 0x06FF): "Arabic",
            (0x0750, 0x077F): "Arabic Supplement", 
            (0x08A0, 0x08FF): "Arabic Extended-A",
            (0xFB50, 0xFDFF): "Arabic Presentation Forms-A",
            (0xFE70, 0xFEFF): "Arabic Presentation Forms-B"
        }
        
        found_blocks = set()
        for char in arabic_text:
            code_point = ord(char)
            for (start, end), block_name in arabic_ranges.items():
                if start <= code_point <= end:
                    found_blocks.add(block_name)
        
        table.add_row("Unicode Blocks Found", ", ".join(found_blocks) if found_blocks else "None")
        
        # Direction analysis
        has_rtl_chars = any(
            0x0590 <= ord(char) <= 0x08FF or  # Hebrew + Arabic blocks
            0xFB1D <= ord(char) <= 0xFDFF or  # Hebrew + Arabic Presentation Forms-A
            0xFE70 <= ord(char) <= 0xFEFF     # Arabic Presentation Forms-B
            for char in arabic_text
        )
        table.add_row("Contains RTL Characters", str(has_rtl_chars))
        
        self.console.print(table)
        
        # Visual display test
        panel = Panel(
            arabic_text,
            title="Arabic Text Display Test",
            subtitle="If this appears garbled or left-to-right, RTL display isn't working properly"
        )
        self.console.print(panel)
    
    async def test_api_response(self):
        """Test the actual API response for RTL content."""
        self.console.print("\n🌐 Testing API Response...")
        
        try:
            async with httpx.AsyncClient() as client:
                # Test translation API
                response = await client.post(
                    f"{self.base_url}/api/v1/translate/",
                    json={
                        "text": "Welcome to LocPlat! Our field mapping system makes it easy to translate complex content structures from Directus CMS.",
                        "source_lang": "en",
                        "target_lang": "ar",
                        "provider": "openai",
                        "model": "gpt-4o-mini",
                        "api_key": os.getenv("OPENAI_API_KEY", "sk-test1234567890abcdefghijk")
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display the full response
                    self.console.print("\n📄 Full API Response:")
                    self.console.print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    # Extract and analyze the Arabic text
                    if "translated_text" in data:
                        arabic_text = data["translated_text"]
                        self.console.print(f"\n🔍 Analyzing Arabic translation:")
                        self.display_arabic_text_analysis(arabic_text)
                        
                        # Verify RTL properties
                        if data.get("language_direction") == "rtl":
                            self.console.print("✅ API correctly identified RTL direction")
                        else:
                            self.console.print("❌ API failed to identify RTL direction")
                        
                        return arabic_text
                    else:
                        self.console.print("❌ No translated_text in response")
                        return None
                else:
                    self.console.print(f"❌ API request failed: {response.status_code}")
                    self.console.print(response.text)
                    return None
                    
        except Exception as e:
            self.console.print(f"❌ Error testing API: {e}")
            return None
    
    def test_rtl_rendering_fixes(self):
        """Provide solutions for RTL display issues."""
        self.console.print("\n🔧 RTL Display Solutions:")
        
        solutions = Table()
        solutions.add_column("Issue", style="red")
        solutions.add_column("Solution", style="green")
        solutions.add_column("Implementation", style="cyan")
        
        solutions.add_row(
            "Terminal doesn't support RTL",
            "Use RTL-aware terminal",
            "Try: iTerm2, Windows Terminal, or modern terminal emulators"
        )
        
        solutions.add_row(
            "Text appears left-to-right",
            "Add Unicode RTL markers",
            "Prefix with \\u202E (RTL override) or \\u061C (Arabic letter mark)"
        )
        
        solutions.add_row(
            "JSON display issues",
            "Use proper JSON formatting",
            "json.dumps() with ensure_ascii=False"
        )
        
        solutions.add_row(
            "Browser display issues",
            "Set proper CSS direction",
            "CSS: direction: rtl; text-align: right; unicode-bidi: bidi-override;"
        )
        
        solutions.add_row(
            "API response formatting",
            "Include direction metadata",
            "Add 'language_direction': 'rtl' and proper Unicode handling"
        )
        
        self.console.print(solutions)
    
    def create_html_test_file(self, arabic_text: str):
        """Create an HTML file for proper RTL display testing."""
        html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LocPlat RTL Display Test</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            direction: rtl;
            text-align: right;
            unicode-bidi: bidi-override;
            padding: 20px;
            line-height: 1.6;
        }}
        .rtl-text {{
            direction: rtl;
            text-align: right;
            background: #f5f5f5;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .ltr-text {{
            direction: ltr;
            text-align: left;
            background: #e8f4f8;
            padding: 15px;
            border: 1px solid #b3d9e8;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .comparison {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        .comparison > div {{
            flex: 1;
        }}
        h1, h2 {{
            color: #333;
        }}
        .json-display {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            overflow-x: auto;
            direction: ltr;
            text-align: left;
        }}
    </style>
</head>
<body>
    <h1>LocPlat RTL Display Test</h1>
    
    <h2>Original English Text</h2>
    <div class="ltr-text">
        Welcome to LocPlat! Our field mapping system makes it easy to translate complex content structures from Directus CMS.
    </div>
    
    <h2>Arabic Translation (RTL)</h2>
    <div class="rtl-text">
        {arabic_text}
    </div>
    
    <h2>Mixed Direction Test</h2>
    <div class="comparison">
        <div>
            <h3>Forced LTR (Wrong)</h3>
            <div class="ltr-text" style="direction: ltr; text-align: left;">
                {arabic_text}
            </div>
        </div>
        <div>
            <h3>Proper RTL (Correct)</h3>
            <div class="rtl-text">
                {arabic_text}
            </div>
        </div>
    </div>
    
    <h2>API Response JSON</h2>
    <div class="json-display">{{
    "translated_text": "{arabic_text}",
    "provider_used": "openai",
    "model_used": "gpt-4o-mini",
    "source_lang": "en",
    "target_lang": "ar",
    "quality_score": 0.9,
    "language_direction": "rtl"
}}</div>
    
    <h2>Character Analysis</h2>
    <table border="1" style="width: 100%; border-collapse: collapse;">
        <tr>
            <th>Property</th>
            <th>Value</th>
        </tr>
        <tr>
            <td>Character Count</td>
            <td>{len(arabic_text)}</td>
        </tr>
        <tr>
            <td>Byte Length (UTF-8)</td>
            <td>{len(arabic_text.encode('utf-8'))}</td>
        </tr>
        <tr>
            <td>Contains Arabic Unicode</td>
            <td>{'Yes' if any(0x0600 <= ord(c) <= 0x06FF for c in arabic_text) else 'No'}</td>
        </tr>
    </table>
    
    <h2>Instructions</h2>
    <div class="ltr-text" style="direction: ltr;">
        <strong>If the Arabic text appears correctly above (flowing right-to-left), your RTL display is working.</strong><br>
        <strong>If it appears left-to-right or garbled, you need to:</strong>
        <ul>
            <li>Use an RTL-capable browser or terminal</li>
            <li>Ensure proper Unicode support</li>
            <li>Set correct CSS direction properties</li>
            <li>Use proper font that supports Arabic characters</li>
        </ul>
    </div>
</body>
</html>"""
        
        html_file_path = "/Users/jneaimimacmini/dev/python/locplat/rtl_display_test.html"
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.console.print(f"\n📄 Created HTML test file: {html_file_path}")
        self.console.print("🌐 Open this file in a browser for proper RTL display testing")
        
        return html_file_path
    
    async def run_complete_test(self):
        """Run the complete RTL display test suite."""
        self.console.print(Panel("🚀 LocPlat RTL Display Test Suite", style="bold blue"))
        
        # Step 1: Check system RTL support
        self.console.print("\n1️⃣ Checking System RTL Support...")
        rtl_supported = self.check_system_rtl_support()
        
        # Step 2: Test API response
        self.console.print("\n2️⃣ Testing API Translation Response...")
        arabic_text = await self.test_api_response()
        
        if arabic_text:
            # Step 3: Create HTML test file
            self.console.print("\n3️⃣ Creating HTML Test File...")
            html_file = self.create_html_test_file(arabic_text)
            
            # Step 4: Provide solutions
            self.console.print("\n4️⃣ RTL Display Solutions...")
            self.test_rtl_rendering_fixes()
            
            # Summary
            self.console.print(Panel(
                f"✅ Test completed successfully!\n\n"
                f"📄 Arabic Text: {arabic_text[:50]}...\n"
                f"🌐 HTML Test File: {html_file}\n"
                f"💡 Open the HTML file in your browser for proper RTL display testing",
                title="Test Summary",
                style="green"
            ))
        else:
            self.console.print(Panel(
                "❌ Could not retrieve Arabic translation from API.\n"
                "Please check that the server is running and you have valid API keys.",
                title="Test Failed",
                style="red"
            ))


async def main():
    """Main function to run RTL display tests."""
    tester = RTLDisplayTester()
    await tester.run_complete_test()


if __name__ == "__main__":
    asyncio.run(main())
