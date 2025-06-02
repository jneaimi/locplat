"""
Abstract translation provider interface and base classes for AI translation services.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import asyncio
import logging
import re

logger = logging.getLogger(__name__)


class LanguageDirection(Enum):
    """Language text direction enumeration."""
    LTR = "ltr"  # Left-to-right
    RTL = "rtl"  # Right-to-left


class TranslationQuality(Enum):
    """Translation quality assessment levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class TranslationError(Exception):
    """Base exception for translation errors."""
    pass


class ProviderError(TranslationError):
    """Exception raised when a specific provider fails."""
    def __init__(self, provider_name: str, message: str, original_error: Exception = None):
        self.provider_name = provider_name
        self.original_error = original_error
        super().__init__(f"{provider_name}: {message}")



class TranslationResult:
    """Result object for translation operations."""
    def __init__(
        self,
        translated_text: str,
        provider_used: str,
        source_lang: str,
        target_lang: str,
        quality_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.translated_text = translated_text
        self.provider_used = provider_used
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.quality_score = quality_score
        self.metadata = metadata or {}



class TranslationProvider(ABC):
    """Abstract base class for all translation providers."""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        api_key: str,
        context: Optional[str] = None
    ) -> str:
        """
        Translate a single text string.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'ar', 'bs')
            api_key: Provider-specific API key
            context: Optional context for better translation

        Returns:
            Translated text string

        Raises:
            ProviderError: If translation fails
        """
        pass

    @abstractmethod
    async def batch_translate(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        api_key: str,
        context: Optional[str] = None
    ) -> List[str]:
        """
        Translate multiple text strings in a batch operation.

        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            api_key: Provider-specific API key
            context: Optional context for better translation

        Returns:
            List of translated text strings in the same order

        Raises:
            ProviderError: If translation fails
        """
        pass

    @abstractmethod
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate the provided API key."""
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes for this provider."""
        pass

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return self.name

    def supports_language_pair(self, source_lang: str, target_lang: str) -> bool:
        """Check if provider supports the given language pair."""
        supported = self.get_supported_languages()
        return source_lang in supported and target_lang in supported

    def get_language_direction(self, lang_code: str) -> LanguageDirection:
        """Get the text direction for a language code."""
        rtl_languages = {'ar', 'he', 'fa', 'ur', 'yi', 'ji', 'iw', 'ku', 'ps', 'sd'}
        return (LanguageDirection.RTL if lang_code.lower() in rtl_languages 
                else LanguageDirection.LTR)

    def _sanitize_text(self, text: str, max_chars: int = 2000) -> str:
        """
        Sanitize user input to prevent prompt injection attacks and token limit exceeded errors.

        Args:
            text: User input text to sanitize
            max_chars: Maximum allowed characters (default: 2000)

        Returns:
            Sanitized text safe for use in prompts
        """
        if not text:
            return ""

        # Truncate to maximum length first
        sanitized = text[:max_chars]

        # Remove control characters that could cause issues
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', sanitized)

        # Remove potential prompt injection patterns
        injection_patterns = [
            r'(?i)ignore\s+(?:previous|all|above|prior)\s+(?:instructions?|prompts?|context)',
            r'(?i)(?:system|assistant|user)\s*:',
            r'(?i)(?:new|different|alternative)\s+(?:instructions?|prompts?|task)',
            r'(?i)(?:act|behave|pretend)\s+(?:as|like)\s+(?:a\s+)?(?:different|new)',
            r'(?i)(?:forget|ignore|disregard|override)\s+(?:everything|all)',
            r'(?i)jailbreak|prompt\s*injection|adversarial',
        ]

        for pattern in injection_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)

        # Clean up excessive whitespace but preserve line breaks for readability
        sanitized = re.sub(r'\n\s*\n\s*\n+', '\n\n', sanitized)  # Max 2 consecutive newlines
        sanitized = re.sub(r'[ \t]+', ' ', sanitized)  # Normalize whitespace

        return sanitized.strip()

    def _sanitize_context(self, context: str, max_chars: int = 500) -> str:
        """
        Sanitize context input with stricter limits.

        Args:
            context: Context text to sanitize
            max_chars: Maximum allowed characters for context (default: 500)

        Returns:
            Sanitized context text
        """
        if not context:
            return ""

        return self._sanitize_text(context, max_chars)

    def assess_translation_quality(
        self, original: str, translation: str, source_lang: str, target_lang: str
    ) -> float:
        """Assess translation quality (basic implementation)."""
        if not translation or not original:
            return 0.0

        length_ratio = len(translation) / len(original)
        if length_ratio < 0.3 or length_ratio > 3.0:
            return 0.3
        if translation.lower() == original.lower():
            return 0.2

        base_score = 0.7
        if 0.5 <= length_ratio <= 2.0:
            base_score = 0.8
        if 0.7 <= length_ratio <= 1.5:
            base_score = 0.9

        return base_score

    def optimize_prompt_for_provider(
        self, text: str, source_lang: str, target_lang: str, context: Optional[str] = None
    ) -> str:
        """Optimize translation prompt for the specific provider with input sanitization."""
        # Sanitize inputs to prevent prompt injection attacks
        safe_text = self._sanitize_text(text)
        safe_context = self._sanitize_context(context) if context else None

        # Validate that we still have meaningful content after sanitization
        if not safe_text.strip():
            raise ProviderError(self.name, "Text content invalid or empty after sanitization")

        lang_names = {'en': 'English', 'ar': 'Arabic', 'bs': 'Bosnian'}
        source_name = lang_names.get(source_lang, source_lang.upper())
        target_name = lang_names.get(target_lang, target_lang.upper())

        # Check if this is an HTML fragment translation (indicated by specific context)
        is_html_fragment = safe_context and "HTML fragment translation" in safe_context

        if is_html_fragment:
            # For HTML fragments, be very strict about only translating the exact content
            prompt = f"Translate this {source_name} text fragment to {target_name}. Translate ONLY the given text, do not add any extra words or content:"
        else:
            # Standard translation prompt
            prompt = f"Translate the following {source_name} text to {target_name}:"
            
            if target_lang == 'ar' and not is_html_fragment:
                prompt += " Please maintain cultural sensitivity and appropriate formal register."
            if target_lang == 'bs':
                prompt += " Use Latin script unless otherwise specified."
        
        if safe_context and not is_html_fragment:
            prompt += f" Context: {safe_context}"
        elif is_html_fragment:
            # For HTML fragments, just add a note about preserving meaning
            prompt += " Preserve the exact meaning."

        prompt += f"\n\nText to translate: {safe_text}"
        return prompt


class BaseAsyncProvider(TranslationProvider):
    """Base class for async translation providers with common functionality."""
    
    async def batch_translate(
        self, 
        texts: List[str], 
        source_lang: str, 
        target_lang: str, 
        api_key: str,
        context: Optional[str] = None
    ) -> List[str]:
        """Common batch translation implementation."""
        if not texts:
            return []
        
        # For batch operations, use concurrent translation
        tasks = [
            self.translate(text, source_lang, target_lang, api_key, context)
            for text in texts
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            translations = []
            for result in results:
                if isinstance(result, Exception):
                    raise result
                translations.append(result)
            return translations
        except Exception as e:
            raise ProviderError(self.name, f"Batch translation failed: {str(e)}", e) from e
