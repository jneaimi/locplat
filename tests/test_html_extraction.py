#!/usr/bin/env python3
"""
Test HTML text extraction and reassembly logic.
"""
from bs4 import BeautifulSoup

def test_html_extraction():
    """Test the HTML text extraction and reassembly."""
    # Original HTML
    html = '<p>Introduction: AI is transforming <em>multilingual content management</em>. Key benefits include real-time processing.</p>'
    
    print(f"Original HTML: {html}")
    print("\n--- Testing Text Extraction ---")
    
    # Extract text nodes (simplified version of field_mapper logic)
    soup = BeautifulSoup(html, 'html.parser')
    text_nodes = []
    
    for element in soup.find_all(text=True):
        text_content = element.strip()
        if text_content:
            text_nodes.append({
                'text': text_content,
                'parent_tag': element.parent.name if element.parent else None,
                'parent_attrs': element.parent.attrs if element.parent else {}
            })
            print(f"Found text: '{text_content}' in <{element.parent.name}>")
    
    print(f"\nTotal text nodes found: {len(text_nodes)}")
    
    # Simulate translations
    translated_nodes = []
    for node in text_nodes:
        if "multilingual content management" in node['text']:
            translated_text = node['text'].replace("multilingual content management", "إدارة المحتوى متعدد اللغات")
        else:
            translated_text = f"[AR] {node['text']}"  # Simulate Arabic translation
        
        translated_nodes.append({
            'text': node['text'],
            'translated_text': translated_text,
            'parent_tag': node['parent_tag'],
            'parent_attrs': node['parent_attrs']
        })
        print(f"'{node['text']}' -> '{translated_text}'")
    
    print("\n--- Testing Reassembly ---")
    
    # Reassemble HTML (simplified version)
    soup = BeautifulSoup(html, 'html.parser')
    text_mapping = {}
    for node in translated_nodes:
        text_mapping[node['text']] = node['translated_text']
    
    for element in soup.find_all(text=True):
        text_content = element.strip()
        if text_content and text_content in text_mapping:
            element.replace_with(text_mapping[text_content])
    
    result = str(soup)
    print(f"Reassembled HTML: {result}")
    
    # Check if "multilingual content management" was translated
    if "multilingual content management" not in result:
        print("✅ SUCCESS: Text inside HTML tags was properly translated!")
    else:
        print("❌ ISSUE: Text inside HTML tags was NOT translated")

if __name__ == "__main__":
    test_html_extraction()
