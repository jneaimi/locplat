"""
Cache Integration Service

Provides cached translation service that integrates with existing AI providers.
This service acts as a middleware layer between the API endpoints and AI providers.
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.ai_response_cache import get_cache
from app.services.provider_router import ProviderRouter
from app.services.translation_provider import TranslationRequest, TranslationResponse

logger = logging.getLogger(__name__)


class CachedTranslationService:
    """
    Translation service with intelligent caching.
    
    This service wraps the existing provider router and adds caching capabilities.
    """
    
    def __init__(self):
        self.provider_router = ProviderRouter()
    
    async def translate_with_cache(
        self,
        request: TranslationRequest,
        collection: Optional[str] = None,
        content_type: str = 'standard',
        confidence: float = 1.0
    ) -> TranslationResponse:
        """Translate text with caching support."""
        cache = await get_cache()
        
        # Try each provider in the cascade until we get a response
        providers = ['openai', 'anthropic', 'mistral', 'deepseek']
        
        for provider in providers:
            try:
                # Check cache first
                cached_response = await cache.get_cached_response(
                    prompt=request.content,
                    provider=provider,
                    model=self._get_default_model(provider),
                    collection=collection,
                    target_language=request.target_language
                )
                
                if cached_response:
                    logger.info(f"Cache hit for {provider}")
                    return TranslationResponse(
                        translated_content=cached_response,
                        source_language=request.source_language,
                        target_language=request.target_language,
                        provider=provider,
                        model=self._get_default_model(provider),
                        confidence_score=confidence
                    )
                
                # Cache miss - try the provider
                try:
                    response = await self.provider_router.translate(request, provider)
                    
                    if response and response.translated_content:
                        # Cache the successful response
                        await cache.cache_response(
                            prompt=request.content,
                            provider=provider,
                            model=response.model or self._get_default_model(provider),
                            response=response.translated_content,
                            collection=collection,
                            target_language=request.target_language,
                            content_type=content_type,
                            confidence=confidence
                        )
                        
                        logger.info(f"Translation successful with {provider}, cached for future use")
                        return response
                        
                except Exception as e:
                    logger.warning(f"Provider {provider} failed: {e}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error with provider {provider}: {e}")
                continue
        
        # If all providers failed, raise an exception
        raise Exception("All translation providers failed")
    
    def _get_default_model(self, provider: str) -> str:
        """Get default model for a provider."""
        defaults = {
            'openai': 'gpt-3.5-turbo',
            'anthropic': 'claude-3-haiku',
            'mistral': 'mistral-small',
            'deepseek': 'deepseek-chat'
        }
        return defaults.get(provider, 'unknown')
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache = await get_cache()
        return await cache.get_cache_stats()
    
    async def invalidate_cache_for_collection(self, collection: str) -> int:
        """Invalidate cache for a specific Directus collection."""
        cache = await get_cache()
        return await cache.invalidate_cache(collection=collection)
    
    async def warm_cache_for_common_content(self, content_list: List[Dict[str, Any]]) -> int:
        """Warm cache with commonly used content."""
        cache = await get_cache()
        return await cache.warm_cache(content_list)
