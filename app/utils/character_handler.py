"""
Character handling utility for proper Unicode support and special character preservation.
Focuses on Bosnian, Croatian, Serbian, and other Slavic languages with diacritical marks.
"""
import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Script(Enum):
    """Script types for multi-script languages."""
    LATIN = "latin"
    CYRILLIC = "cyrillic"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class CharacterValidationResult:
    """Result of character validation with details about issues found."""
    
    def __init__(self):
        self.is_valid = True
        self.encoding_issues: List[str] = []
        self.normalization_issues: List[str] = []
        self.special_chars_found: Set[str] = set()
        self.script_detected: Script = Script.UNKNOWN
        self.warnings: List[str] = []
        self.repaired_text: Optional[str] = None


class CharacterHandler:
    """Handler for special character processing, validation, and preservation."""
    
    def __init__(self):
        # Bosnian special characters (both cases)
        self.bosnian_chars = {
            'č', 'ć', 'đ', 'š', 'ž',  # lowercase
            'Č', 'Ć', 'Đ', 'Š', 'Ž'   # uppercase
        }
        
        # Extended Slavic characters for other languages
        self.slavic_chars = {
            # Croatian (same as Bosnian)
            'č', 'ć', 'đ', 'š', 'ž', 'Č', 'Ć', 'Đ', 'Š', 'Ž',
            # Serbian additional Cyrillic
            'љ', 'њ', 'џ', 'Љ', 'Њ', 'Џ',            # Polish
            'ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż',
            'Ą', 'Ć', 'Ę', 'Ł', 'Ń', 'Ó', 'Ś', 'Ź', 'Ż',
            # Czech
            'á', 'č', 'ď', 'é', 'ě', 'í', 'ň', 'ó', 'ř', 'š', 'ť', 'ú', 'ů', 'ý', 'ž',
            'Á', 'Č', 'Ď', 'É', 'Ě', 'Í', 'Ň', 'Ó', 'Ř', 'Š', 'Ť', 'Ú', 'Ů', 'Ý', 'Ž'
        }
        
        # Cyrillic script detection patterns
        self.cyrillic_range = re.compile(r'[\u0400-\u04FF\u0500-\u052F]')
        self.latin_range = re.compile(r'[A-Za-z\u0100-\u017F\u1E00-\u1EFF]')
        
        # Common encoding issues and their fixes
        self.encoding_fixes = {
            # Double-encoded UTF-8 sequences
            'Ä\x8d': 'č', 'Ä\x87': 'ć', 'Ä\x91': 'đ', 'Å¡': 'š', 'Å¾': 'ž',
            'Ä\x8c': 'Č', 'Ä\x86': 'Ć', 'Ä\x90': 'Đ', 'Å ': 'Š', 'Å½': 'Ž',
            # Windows-1252 to UTF-8 (only for actual problematic sequences)
            'Äś': 'č'
        }
        
        # Bosnian Latin-Cyrillic mapping
        self.latin_to_cyrillic = {
            'a': 'а', 'b': 'б', 'c': 'ц', 'č': 'ч', 'ć': 'ћ', 'd': 'д', 'đ': 'ђ',
            'e': 'е', 'f': 'ф', 'g': 'г', 'h': 'х', 'i': 'и', 'j': 'ј', 'k': 'к',
            'l': 'л', 'lj': 'љ', 'm': 'м', 'n': 'н', 'nj': 'њ', 'o': 'о', 'p': 'п',
            'r': 'р', 's': 'с', 'š': 'ш', 't': 'т', 'u': 'у', 'v': 'в', 'z': 'з',
            'ž': 'ж',
            # Uppercase
            'A': 'А', 'B': 'Б', 'C': 'Ц', 'Č': 'Ч', 'Ć': 'Ћ', 'D': 'Д', 'Đ': 'Ђ',
            'E': 'Е', 'F': 'Ф', 'G': 'Г', 'H': 'Х', 'I': 'И', 'J': 'Ј', 'K': 'К',
            'L': 'Л', 'LJ': 'Љ', 'M': 'М', 'N': 'Н', 'NJ': 'Њ', 'O': 'О', 'P': 'П',
            'R': 'Р', 'S': 'С', 'Š': 'Ш', 'T': 'Т', 'U': 'У', 'V': 'В', 'Z': 'З',
            'Ž': 'Ж'
        }
        
        # Reverse mapping
        self.cyrillic_to_latin = {v: k for k, v in self.latin_to_cyrillic.items()}
        
        # Character substitution fallbacks for degraded environments
        self.fallback_substitutions = {
            'č': 'c', 'ć': 'c', 'đ': 'd', 'š': 's', 'ž': 'z',
            'Č': 'C', 'Ć': 'C', 'Đ': 'D', 'Š': 'S', 'Ž': 'Z',
            'ą': 'a', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
            'Ą': 'A', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
        }
    
    def validate_text_encoding(self, text: str) -> CharacterValidationResult:
        """
        Validate text encoding and detect potential issues.
        
        Args:
            text: Text to validate
            
        Returns:
            CharacterValidationResult with validation details
        """
        result = CharacterValidationResult()
        
        if not text:
            return result
        
        try:
            # Test if text is properly encoded UTF-8
            text.encode('utf-8').decode('utf-8')
        except UnicodeEncodeError as e:
            result.is_valid = False
            result.encoding_issues.append(f"Unicode encoding error: {str(e)}")
            logger.warning(f"Text encoding validation failed: {e}")
        
        # Check for double-encoded sequences
        for bad_seq, good_char in self.encoding_fixes.items():
            if bad_seq in text:
                result.encoding_issues.append(f"Double-encoded sequence found: {bad_seq} → {good_char}")
                if result.repaired_text is None:
                    result.repaired_text = text
                result.repaired_text = result.repaired_text.replace(bad_seq, good_char)
        
        # Check normalization form
        if unicodedata.normalize('NFC', text) != text:
            result.normalization_issues.append("Text is not in NFC normalization form")
            if result.repaired_text is None:
                result.repaired_text = text
            result.repaired_text = unicodedata.normalize('NFC', result.repaired_text or text)
        
        # Detect special characters
        result.special_chars_found = self.find_special_characters(text)
        
        # Detect script
        result.script_detected = self.detect_script(text)
        
        # Check for potential issues with special character sequences
        self._check_character_combinations(text, result)
        
        return result
    
    def find_special_characters(self, text: str) -> Set[str]:
        """Find all special characters in text."""
        special_chars = set()
        
        for char in text:
            if char in self.slavic_chars:
                special_chars.add(char)
        
        return special_chars
    
    def detect_script(self, text: str) -> Script:
        """
        Detect the script used in the text (Latin, Cyrillic, or mixed).
        
        Args:
            text: Text to analyze
            
        Returns:
            Script enum value
        """
        has_latin = bool(self.latin_range.search(text))
        has_cyrillic = bool(self.cyrillic_range.search(text))
        
        if has_latin and has_cyrillic:
            return Script.MIXED
        elif has_cyrillic:
            return Script.CYRILLIC
        elif has_latin:
            return Script.LATIN
        else:
            return Script.UNKNOWN
    
    def normalize_text(self, text: str, form: str = 'NFC') -> str:
        """
        Normalize text to a specific Unicode normalization form.
        
        Args:
            text: Text to normalize
            form: Normalization form ('NFC', 'NFD', 'NFKC', 'NFKD')
            
        Returns:
            Normalized text
        """
        try:
            return unicodedata.normalize(form, text)
        except Exception as e:
            logger.warning(f"Text normalization failed: {e}")
            return text
    
    def repair_encoding_issues(self, text: str) -> str:
        """
        Attempt to repair common encoding issues.
        
        Args:
            text: Text with potential encoding issues
            
        Returns:
            Repaired text
        """
        repaired = text
        
        # Fix common double-encoded sequences
        for bad_seq, good_char in self.encoding_fixes.items():
            repaired = repaired.replace(bad_seq, good_char)
        
        # Normalize to NFC form
        repaired = self.normalize_text(repaired, 'NFC')
        
        return repaired
    
    def transliterate_to_latin(self, text: str) -> str:
        """
        Transliterate Cyrillic text to Latin script (for Bosnian/Serbian).
        
        Args:
            text: Text in Cyrillic script
            
        Returns:
            Text in Latin script
        """
        result = text
        
        # Handle digraphs first (longer sequences)
        for cyrillic, latin in self.cyrillic_to_latin.items():
            if len(cyrillic) > 1:  # Handle digraphs like 'љ' → 'lj'
                result = result.replace(cyrillic, latin)
        
        # Handle single characters
        for cyrillic, latin in self.cyrillic_to_latin.items():
            if len(cyrillic) == 1:
                result = result.replace(cyrillic, latin)
        
        return result
    
    def transliterate_to_cyrillic(self, text: str) -> str:
        """
        Transliterate Latin text to Cyrillic script (for Bosnian/Serbian).
        
        Args:
            text: Text in Latin script
            
        Returns:
            Text in Cyrillic script
        """
        result = text
        
        # Handle digraphs first (longer sequences like 'lj', 'nj')
        result = re.sub(r'lj', 'љ', result, flags=re.IGNORECASE)
        result = re.sub(r'nj', 'њ', result, flags=re.IGNORECASE)
        result = re.sub(r'LJ', 'Љ', result)
        result = re.sub(r'NJ', 'Њ', result)
        
        # Handle single characters
        for latin, cyrillic in self.latin_to_cyrillic.items():
            if len(latin) == 1:
                result = result.replace(latin, cyrillic)
        
        return result
    
    def apply_fallback_substitutions(self, text: str) -> str:
        """
        Apply fallback character substitutions for degraded environments.
        
        Args:
            text: Text with special characters
            
        Returns:
            Text with ASCII fallbacks
        """
        result = text
        
        for special_char, fallback in self.fallback_substitutions.items():
            result = result.replace(special_char, fallback)
        
        return result
    
    def preserve_special_characters(self, original: str, translated: str) -> Tuple[str, List[str]]:
        """
        Ensure special characters from original text are preserved in translation.
        
        Args:
            original: Original text with special characters
            translated: Translated text that might be missing special characters
            
        Returns:
            Tuple of (corrected_translation, list_of_corrections_made)
        """
        corrections = []
        original_chars = self.find_special_characters(original)
        translated_chars = self.find_special_characters(translated)
        
        # If no special characters in original, nothing to preserve
        if not original_chars:
            return translated, corrections
        
        # Check if translation lost special characters
        missing_chars = original_chars - translated_chars
        
        if missing_chars:
            logger.warning(f"Translation lost special characters: {missing_chars}")
            corrections.append(f"Missing special characters detected: {', '.join(missing_chars)}")
        
        # For now, return as-is with warnings
        # In a more sophisticated implementation, we could try to:
        # 1. Map similar words between original and translation
        # 2. Restore special characters in corresponding positions
        # 3. Use dictionary-based correction
        
        return translated, corrections
    
    def create_character_mapping_report(self, text: str) -> Dict[str, any]:
        """
        Create a detailed report of character usage in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with character analysis
        """
        special_chars = self.find_special_characters(text)
        script = self.detect_script(text)
        validation = self.validate_text_encoding(text)
        
        return {
            'text_length': len(text),
            'special_characters_found': list(special_chars),
            'special_character_count': len(special_chars),
            'script_detected': script.value,
            'encoding_valid': validation.is_valid,
            'encoding_issues': validation.encoding_issues,
            'normalization_issues': validation.normalization_issues,
            'warnings': validation.warnings,
            'unicode_categories': self._analyze_unicode_categories(text),
            'has_rtl_marks': self._has_rtl_marks(text)
        }
    
    def _check_character_combinations(self, text: str, result: CharacterValidationResult):
        """Check for problematic character combinations."""
        # Check for mixed encoding patterns
        if re.search(r'[Ã¡Ã©Ã­Ã³Ãº]', text):
            result.warnings.append("Possible ISO-8859-1 to UTF-8 encoding issue detected")
        
        # Check for suspicious byte sequences
        if re.search(r'[\xc2-\xc3][\x80-\xbf]', text):
            result.warnings.append("Possible byte-level encoding issue detected")
    
    def _analyze_unicode_categories(self, text: str) -> Dict[str, int]:
        """Analyze Unicode categories in text."""
        categories = {}
        for char in text:
            category = unicodedata.category(char)
            categories[category] = categories.get(category, 0) + 1
        return categories
    
    def _has_rtl_marks(self, text: str) -> bool:
        """Check if text contains RTL marks."""
        rtl_marks = ['\u200f', '\u202e', '\u202d']  # RLM, RLO, LRO
        return any(mark in text for mark in rtl_marks)


# Global instance for easy access
character_handler = CharacterHandler()
