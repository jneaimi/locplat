"""
Flexible translation service for dynamic provider/model selection.
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


class FlexibleTranslationService:
    """Flexible translation service with dynamic provider/model selection."""
    
    def __init__(self):
        """Initialize the translation service with all available providers."""
        self._providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "mistral": MistralProvider(),
            "deepseek": DeepSeekProvider()
        }
        logger.info(f"Initialized FlexibleTranslationService with providers: {list(self._providers.keys())}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self._providers.keys())
    
    def get_provider_models(self) -> Dict[str, Dict[str, Any]]:
        """Get available models for each provider."""
        return {
            "openai": {
                "models": {
                    "gpt-4o-mini": {"cost": "low", "quality": "high", "speed": "fast"},
                    "gpt-4o": {"cost": "medium", "quality": "very_high", "speed": "medium"},
                    "gpt-4-turbo": {"cost": "high", "quality": "very_high", "speed": "medium"},
                    "gpt-3.5-turbo": {"cost": "very_low", "quality": "medium", "speed": "very_fast"}
                },
                "default": "gpt-4o-mini"
            },
            "anthropic": {
                "models": {
                    "claude-3-haiku-20240307": {"cost": "low", "quality": "high", "speed": "very_fast"},
                    "claude-3-sonnet-20240229": {"cost": "medium", "quality": "very_high", "speed": "medium"},
                    "claude-3-opus-20240229": {"cost": "very_high", "quality": "excellent", "speed": "slow"}
                },
                "default": "claude-3-haiku-20240307"
            },
            "mistral": {
                "models": {
                    "mistral-small": {"cost": "low", "quality": "medium", "speed": "fast"},
                    "mistral-medium": {"cost": "medium", "quality": "high", "speed": "medium"},
                    "mistral-large": {"cost": "high", "quality": "very_high", "speed": "medium"}
                },
                "default": "mistral-small"
            },
            "deepseek": {
                "models": {
                    "deepseek-chat": {"cost": "very_low", "quality": "medium", "speed": "fast"},
                    "deepseek-coder": {"cost": "very_low", "quality": "medium", "speed": "fast"}
                },
                "default": "deepseek-chat"
            }
        }
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str, 
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        context: Optional[str] = None
    ) -> TranslationResult:
        """
        Translate text using specified provider and model.
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'ar', 'bs')
            provider: Provider name ('openai', 'anthropic', 'mistral', 'deepseek')
            api_key: API key for the specified provider
            model: Model name (optional, uses default if not specified)
            context: Optional context for better translation
            
        Returns:
            TranslationResult with translated text and metadata
            
        Raises:
            TranslationError: If translation fails
        """
        if not text.strip():
            raise TranslationError("Empty text provided for translation")
        
        if provider not in self._providers:
            raise TranslationError(f"Unknown provider: {provider}. Available: {list(self._providers.keys())}")
        
        translation_provider = self._providers[provider]
        
        # Check language support
        if not translation_provider.supports_language_pair(source_lang, target_lang):
            raise TranslationError(f"Provider {provider} does not support language pair {source_lang}->{target_lang}")
        
        try:
            logger.info(f"Translating with {provider} (model: {model or 'default'})")
            
            # For providers that support model specification, we'll update them to handle it
            translated_text = await translation_provider.translate(
                text, 
                source_lang, 
                target_lang, 
                api_key,
                context
            )
            
            # Assess translation quality
            quality_score = await translation_provider.assess_translation_quality(
                text, translated_text, source_lang, target_lang
            )
            
            logger.info(f"Translation successful with {provider} (quality: {quality_score:.2f})")
            
            return TranslationResult(
                translated_text=translated_text,
                provider_used=provider,
                source_lang=source_lang,
                target_lang=target_lang,
                quality_score=quality_score,
                metadata={
                    "model_used": model or "default",
                    "language_direction": translation_provider.get_language_direction(target_lang).value,
                    "context_used": context is not None,
                    "provider_info": self.get_provider_models().get(provider, {})
                }
            )
            
        except ProviderError as e:
            logger.error(f"Provider {provider} failed: {str(e)}")
            raise TranslationError(f"Translation failed with {provider}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error with {provider}: {str(e)}")
            raise TranslationError(f"Unexpected error with {provider}: {str(e)}")
    
    async def batch_translate(
        self, 
        texts: List[str], 
        source_lang: str, 
        target_lang: str,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[TranslationResult]:
        """
        Translate multiple texts using specified provider and model.
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            provider: Provider name
            api_key: API key for the specified provider
            model: Model name (optional)
            context: Optional context for better translation
            
        Returns:
            List of TranslationResult objects
            
        Raises:
            TranslationError: If translation fails
        """
        if not texts:
            return []
        
        if provider not in self._providers:
            raise TranslationError(f"Unknown provider: {provider}. Available: {list(self._providers.keys())}")
        
        translation_provider = self._providers[provider]
        
        # Check language support
        if not translation_provider.supports_language_pair(source_lang, target_lang):
            raise TranslationError(f"Provider {provider} does not support language pair {source_lang}->{target_lang}")
        
        try:
            logger.info(f"Batch translating {len(texts)} texts with {provider} (model: {model or 'default'})")
            
            translated_texts = await translation_provider.batch_translate(
                texts, source_lang, target_lang, api_key, context
            )
            
            # Create results for each translation
            results = []
            for i, (original, translated) in enumerate(zip(texts, translated_texts)):
                quality_score = await translation_provider.assess_translation_quality(
                    original, translated, source_lang, target_lang
                )
                
                results.append(TranslationResult(
                    translated_text=translated,
                    provider_used=provider,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    quality_score=quality_score,
                    metadata={
                        "model_used": model or "default",
                        "batch_index": i,
                        "batch_size": len(texts),
                        "language_direction": translation_provider.get_language_direction(target_lang).value,
                        "context_used": context is not None,
                        "provider_info": self.get_provider_models().get(provider, {})
                    }
                ))
            
            logger.info(f"Batch translation successful with {provider}")
            return results
            
        except ProviderError as e:
            logger.error(f"Batch translation failed with {provider}: {str(e)}")
            raise TranslationError(f"Batch translation failed with {provider}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in batch translation with {provider}: {str(e)}")
            raise TranslationError(f"Unexpected error in batch translation with {provider}: {str(e)}")
    
    async def validate_api_key(self, provider: str, api_key: str) -> bool:
        """
        Validate API key for a specific provider.
        
        Args:
            provider: Provider name
            api_key: API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        if provider not in self._providers:
            return False
        
        try:
            return await self._providers[provider].validate_api_key(api_key)
        except Exception as e:
            logger.error(f"Error validating API key for {provider}: {str(e)}")
            return False
    
    def get_supported_languages(self, provider: str) -> List[str]:
        """
        Get supported languages for a specific provider.
        
        Args:
            provider: Provider name
            
        Returns:
            List of supported language codes
        """
        if provider not in self._providers:
            return []
        
        return self._providers[provider].get_supported_languages()
    
    def get_language_direction(self, lang_code: str) -> LanguageDirection:
        """
        Get language direction for a language code.
        
        Args:
            lang_code: Language code (e.g., 'ar', 'en', 'bs')
            
        Returns:
            LanguageDirection (LTR or RTL)
        """
        # Use any provider's implementation (they should all be the same)
        return list(self._providers.values())[0].get_language_direction(lang_code)
    
    async def translate_collection(
        self, 
        collection_data: Dict[str, Any], 
        field_mapping: Dict[str, str],
        source_lang: str, 
        target_lang: str, 
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate a Directus collection using specified provider and model.
        
        Args:
            collection_data: Collection data from Directus
            field_mapping: Mapping of field names to translate
            source_lang: Source language code
            target_lang: Target language code
            provider: Provider name
            api_key: API key for the specified provider
            model: Model name (optional)
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
                            provider,
                            api_key,
                            model,
                            context
                        )
                        translated_data[field_path] = result.translated_text
                        
                        # Add metadata for translation tracking
                        if "_translations" not in translated_data:
                            translated_data["_translations"] = {}
                        
                        translated_data["_translations"][field_path] = {
                            "provider": result.provider_used,
                            "model": result.metadata.get("model_used"),
                            "quality_score": result.quality_score,
                            "source_lang": source_lang,
                            "target_lang": target_lang
                        }
                        
                    except TranslationError as e:
                        logger.error(f"Failed to translate field {field_path}: {str(e)}")
                        # Keep original text if translation fails
                        continue
        
        return translated_data
