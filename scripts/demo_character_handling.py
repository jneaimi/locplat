#!/usr/bin/env python3
"""
Demonstration script for character handling functionality in LocPlat.
Shows how the enhanced character handling works with Bosnian and other Slavic languages.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.character_handler import character_handler
from app.services.enhanced_content_processor import EnhancedContentProcessor

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def demonstrate_character_detection():
    """Demonstrate character detection capabilities."""
    print_section("Character Detection")
    
    test_texts = [
        "Dobar dan! Kako ste danas?",  # No special chars
        "Čovek je čuvar škole u gradu.",  # Bosnian with special chars
        "Željko drži ključeve od škole.",  # More special chars
        "Kraków to piękne miasto w Polsce.",  # Polish
        "Černý kůň běží přes dvůr.",  # Czech
        "Здраво! Како сте данас?"  # Cyrillic
    ]
    
    for text in test_texts:
        special_chars = character_handler.find_special_characters(text)
        script = character_handler.detect_script(text)
        
        print(f"\nText: {text}")
        print(f"Special characters found: {list(special_chars) if special_chars else 'None'}")
        print(f"Script detected: {script.value}")

def demonstrate_encoding_validation():
    """Demonstrate encoding validation and repair."""
    print_section("Encoding Validation & Repair")
    
    # Simulate some encoding issues
    problematic_texts = [
        "Ovo je Ä\x8desto tekst",  # Double-encoded č
        "Pogreška sa Å¡kolom",     # Double-encoded š
        "Validni tekst sa č, š, ž"  # Valid text
    ]
    
    for text in problematic_texts:
        print(f"\nOriginal: {repr(text)}")
        
        # Validate
        validation = character_handler.validate_text_encoding(text)
        print(f"Valid: {validation.is_valid}")
        if validation.encoding_issues:
            print(f"Issues: {validation.encoding_issues}")
        
        # Repair
        repaired = character_handler.repair_encoding_issues(text)
        print(f"Repaired: {repaired}")
        if repaired != text:
            print(f"✓ Encoding issues were fixed")

def demonstrate_transliteration():
    """Demonstrate script transliteration."""
    print_section("Script Transliteration")
    
    latin_text = "Zdravo, kako si danas?"
    print(f"Original Latin: {latin_text}")
    
    # Latin to Cyrillic
    cyrillic = character_handler.transliterate_to_cyrillic(latin_text)
    print(f"To Cyrillic: {cyrillic}")
    
    # Back to Latin
    back_to_latin = character_handler.transliterate_to_latin(cyrillic)
    print(f"Back to Latin: {back_to_latin}")

def demonstrate_character_preservation():
    """Demonstrate character preservation in translation."""
    print_section("Character Preservation Analysis")
    
    original = "Čovek čuva školu u centru grada."
    
    # Good translation (preserves special chars where appropriate)
    good_translation = "Čovjek čuva školu u centru grada."
    
    # Bad translation (lost special chars)
    bad_translation = "Covek cuva skolu u centru grada."
    
    print(f"Original: {original}")
    print(f"\nGood translation: {good_translation}")
    corrected_good, corrections_good = character_handler.preserve_special_characters(
        original, good_translation
    )
    print(f"Corrections needed: {corrections_good if corrections_good else 'None'}")
    
    print(f"\nBad translation: {bad_translation}")
    corrected_bad, corrections_bad = character_handler.preserve_special_characters(
        original, bad_translation
    )
    print(f"Corrections needed: {corrections_bad}")

def demonstrate_content_processor():
    """Demonstrate enhanced content processor."""
    print_section("Enhanced Content Processing")
    
    processor = EnhancedContentProcessor()
    
    # Test with content that has special characters
    content = "Dobrodošli u našu školu! Čuvar će vam pomoći."
    
    print(f"Original content: {content}")
    
    result = processor.preprocess_content(content, 'bs')
    
    print(f"Processed content: {result['content']}")
    print(f"Has special chars: {result['metadata']['has_special_chars']}")
    print(f"Preprocessing applied: {result['metadata']['preprocessing_applied']}")
    
    char_analysis = result['metadata']['character_analysis']
    print(f"Special characters found: {char_analysis['special_characters_found']}")
    print(f"Script detected: {char_analysis['script_detected']}")

def demonstrate_fallback_substitutions():
    """Demonstrate fallback character substitutions."""
    print_section("Fallback Character Substitutions")
    
    text_with_special_chars = "Česta greška sa đavolskim čuvarima u školi."
    
    print(f"Original: {text_with_special_chars}")
    
    fallback = character_handler.apply_fallback_substitutions(text_with_special_chars)
    print(f"With fallbacks: {fallback}")
    print("(For use in systems that don't support special characters)")

def main():
    """Run all demonstrations."""
    print("LocPlat Character Handling Demonstration")
    print("This demo shows enhanced Unicode support for Bosnian and other Slavic languages")
    
    demonstrate_character_detection()
    demonstrate_encoding_validation()
    demonstrate_transliteration()
    demonstrate_character_preservation()
    demonstrate_content_processor()
    demonstrate_fallback_substitutions()
    
    print_section("Summary")
    print("✓ Character detection for Bosnian, Croatian, Serbian, Polish, Czech")
    print("✓ Unicode encoding validation and automatic repair")
    print("✓ Latin ↔ Cyrillic script transliteration")
    print("✓ Character preservation analysis in translations")
    print("✓ Enhanced content processing with character handling")
    print("✓ Fallback substitutions for degraded environments")
    print("\nCharacter handling is now integrated into the translation pipeline!")

if __name__ == "__main__":
    main()
