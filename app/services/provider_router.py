"""
Provider router for cascading fallback translation services.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from .translation_provider import (
    TranslationProvider, 
    TranslationResult, 
    ProviderError, 
    TranslationError,
    LanguageDirection
)
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .mistral_provider import MistralProvider
from .deepseek_provider import DeepSeekProvider

logger = logging.getLogger(__name__)


class ProviderRouter:
    """Router for managing cascading fallback between translation providers."""
    
    def __init__(self):
        """Initialize the provider router with cascading fallback order."""
        self.providers = [
            OpenAIProvider(),      # Primary
            AnthropicProvider(),   # Secondary
            MistralProvider(),     # Tertiary
            DeepSeekProvider()     # Final fallback
        ]
        self.provider_names = [provider.get_provider_name() for provider in self.providers]
        logger.info(f"Initialized ProviderRouter with providers: {self.provider_names}")
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str, 
        api_keys: Dict[str, str],
        context: Optional[str] = None
    ) -> TranslationResult:
        """
        Translate text using cascading fallback through providers.
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'ar', 'bs')
            api_keys: Dictionary of provider API keys {provider_name: api_key}
            context: Optional context for better translation
            
        Returns:
            TranslationResult with translated text and metadata
            
        Raises:
            TranslationError: If all providers fail
        """
        if not text.strip():
            raise TranslationError("Empty text provided for translation")
        
        last_error = None
        attempted_providers = []
        
        for provider in self.providers:
            provider_name = provider.get_provider_name()
            
            # Skip if no API key provided for this provider
            if provider_name not in api_keys or not api_keys[provider_name]:
                logger.debug(f"Skipping {provider_name}: No API key provided")
                continue
            
            # Check if provider supports the language pair
            if not provider.supports_language_pair(source_lang, target_lang):
                logger.debug(f"Skipping {provider_name}: Language pair {source_lang}->{target_lang} not supported")
                continue
            
            try:
                logger.info(f"Attempting translation with {provider_name}")
                
                translated_text = await provider.translate(
                    text, 
                    source_lang, 
                    target_lang, 
                    api_keys[provider_name],
                    context
                )
                
                # Assess translation quality
                quality_score = await provider.assess_translation_quality(
                    text, translated_text, source_lang, target_lang
                )
                
                logger.info(f"Translation successful with {provider_name} (quality: {quality_score:.2f})")
                
                return TranslationResult(
                    translated_text=translated_text,
                    provider_used=provider_name,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    quality_score=quality_score,
                    metadata={
                        "attempted_providers": attempted_providers + [provider_name],
                        "language_direction": provider.get_language_direction(target_lang).value,
                        "context_used": context is not None
                    }
                )
                
            except ProviderError as e:
                attempted_providers.append(provider_name)
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {str(e)}")
                continue
            except Exception as e:
                attempted_providers.append(provider_name)
                last_error = e
                logger.error(f"Unexpected error with {provider_name}: {str(e)}")
                continue
        
        # All providers failed
        error_msg = f"All translation providers failed. Attempted: {attempted_providers}"
        if last_error:
            error_msg += f". Last error: {str(last_error)}"
        
        logger.error(error_msg)
        raise TranslationError(error_msg)
    
    async def batch_translate(
        self, 
        texts: List[str], 
        source_lang: str, 
        target_lang: str,
        api_keys: Dict[str, str],
        context: Optional[str] = None
    ) -> List[TranslationResult]:
        """
        Translate multiple texts using cascading fallback.
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            api_keys: Dictionary of provider API keys
            context: Optional context for better translation
            
        Returns:
            List of TranslationResult objects
            
        Raises:
            TranslationError: If all providers fail for all texts
        """
        if not texts:
            return []
        
        # For batch operations, we'll use the first available provider
        # that works for the entire batch to maintain consistency
        for provider in self.providers:
            provider_name = provider.get_provider_name()
            
            if provider_name not in api_keys or not api_keys[provider_name]:
                continue
            
            if not provider.supports_language_pair(source_lang, target_lang):
                continue
            
            try:
                logger.info(f"Attempting batch translation with {provider_name}")
                
                translated_texts = await provider.batch_translate(
                    texts, source_lang, target_lang, api_keys[provider_name], context
                )
                
                # Create results for each translation
                results = []
                for i, (original, translated) in enumerate(zip(texts, translated_texts)):
                    quality_score = await provider.assess_translation_quality(
                        original, translated, source_lang, target_lang
                    )
                    
                    results.append(TranslationResult(
                        translated_text=translated,
                        provider_used=provider_name,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        quality_score=quality_score,
                        metadata={
                            "batch_index": i,
                            "batch_size": len(texts),
                            "language_direction": provider.get_language_direction(target_lang).value,
                            "context_used": context is not None
                        }
                    ))
                
                logger.info(f"Batch translation successful with {provider_name}")
                return results
                
            except ProviderError as e:
                logger.warning(f"Batch translation failed with {provider_name}: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error in batch translation with {provider_name}: {str(e)}")
                continue
        
        # If batch translation fails, fall back to individual translations
        logger.info("Batch translation failed, falling back to individual translations")
        
        results = []
        for text in texts:
            try:
                result = await self.translate(text, source_lang, target_lang, api_keys, context)
                results.append(result)
            except TranslationError as e:
                logger.error(f"Individual translation failed for text: {text[:50]}...")
                raise e
        
        return results
    
    async def validate_api_keys(self, api_keys: Dict[str, str]) -> Dict[str, bool]:
        """
        Validate API keys for all providers.
        
        Args:
            api_keys: Dictionary of provider API keys
            
        Returns:
            Dictionary mapping provider names to validation status
        """
        validation_results = {}
        
        for provider in self.providers:
            provider_name = provider.get_provider_name()
            
            if provider_name not in api_keys or not api_keys[provider_name]:
                validation_results[provider_name] = False
                continue
            
            try:
                is_valid = await provider.validate_api_key(api_keys[provider_name])
                validation_results[provider_name] = is_valid
                logger.info(f"API key validation for {provider_name}: {'valid' if is_valid else 'invalid'}")
            except Exception as e:
                validation_results[provider_name] = False
                logger.error(f"Error validating API key for {provider_name}: {str(e)}")
        
        return validation_results
    
    def get_supported_languages(self) -> Dict[str, List[str]]:
        """
        Get supported languages for all providers.
        
        Returns:
            Dictionary mapping provider names to supported language lists
        """
        return {
            provider.get_provider_name(): provider.get_supported_languages()
            for provider in self.providers
        }
    
    def get_language_direction(self, lang_code: str) -> LanguageDirection:
        """
        Get language direction for a language code.
        
        Args:
            lang_code: Language code (e.g., 'ar', 'en', 'bs')
            
        Returns:
            LanguageDirection (LTR or RTL)
        """
        # Use the first provider's implementation (they should all be the same)
        return self.providers[0].get_language_direction(lang_code)
    
    def get_available_providers(self, api_keys: Dict[str, str]) -> List[str]:
        """
        Get list of providers that have valid API keys.
        
        Args:
            api_keys: Dictionary of provider API keys
            
        Returns:
            List of provider names with valid API keys
        """
        available = []
        for provider in self.providers:
            provider_name = provider.get_provider_name()
            if provider_name in api_keys and api_keys[provider_name]:
                available.append(provider_name)
        
        return available
    
    async def translate_collection(
        self, 
        collection_data: Dict[str, Any], 
        field_mapping: Dict[str, str],
        source_lang: str, 
        target_lang: str, 
        api_keys: Dict[str, str],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate a Directus collection following field mapping patterns.
        
        Args:
            collection_data: Collection data from Directus
            field_mapping: Mapping of field names to translate
            source_lang: Source language code
            target_lang: Target language code
            api_keys: Dictionary of provider API keys
            context: Optional context for translation
            
        Returns:
            Translated collection data
        """
        translated_data = collection_data.copy()
        
        for field_name, field_path in field_mapping.items():
            if field_path in collection_data:
                text_to_translate = collection_data[field_path]
                
                if isinstance(text_to_translate, str) and text_to_translate.strip():
                    try:
                        result = await self.translate(
                            text_to_translate, 
                            source_lang, 
                            target_lang, 
                            api_keys, 
                            context
                        )
                        translated_data[field_path] = result.translated_text
                        
                        # Add metadata for translation tracking
                        if "_translations" not in translated_data:
                            translated_data["_translations"] = {}
                        
                        translated_data["_translations"][field_path] = {
                            "provider": result.provider_used,
                            "quality_score": result.quality_score,
                            "source_lang": source_lang,
                            "target_lang": target_lang
                        }
                        
                    except TranslationError as e:
                        logger.error(f"Failed to translate field {field_path}: {str(e)}")
                        # Keep original text if translation fails
                        continue
        
        return translated_data
