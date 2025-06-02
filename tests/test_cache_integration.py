"""
Integration test for cache functionality

Tests the cache service integration with real Redis (or mock).
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.services.ai_response_cache import AIResponseCache
from app.services.cached_translation_service import CachedTranslationService
from app.services.translation_provider import TranslationRequest


@pytest.mark.asyncio
async def test_cache_integration():
    """Test cache integration with translation service."""
    # Create cache with mock Redis
    mock_redis = AsyncMock()
    cache = AIResponseCache(redis_client=mock_redis)
    
    # Test basic cache operations
    await cache.cache_response(
        prompt="Hello world",
        provider="openai",
        model="gpt-3.5-turbo",
        response="مرحبا بالعالم"
    )
    
    # Verify set was called
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio  
async def test_cached_translation_service():
    """Test the cached translation service."""
    service = CachedTranslationService()
    
    # Create a test request
    request = TranslationRequest(
        content="Hello world",
        source_language="en",
        target_language="ar"
    )
    
    # Mock the provider router to return a translation
    with patch.object(service.provider_router, 'translate') as mock_translate:
        mock_translate.return_value = type('Response', (), {
            'translated_content': 'مرحبا بالعالم',
            'source_language': 'en',
            'target_language': 'ar',
            'provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'confidence_score': 1.0
        })
        
        # Mock the cache to return None (cache miss)
        with patch('app.services.ai_response_cache.get_cache') as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get_cached_response.return_value = None
            mock_cache.cache_response.return_value = True
            mock_get_cache.return_value = mock_cache
            
            # This should result in a cache miss, translation, and cache store
            response = await service.translate_with_cache(request)
            
            assert response.translated_content == 'مرحبا بالعالم'
            mock_cache.get_cached_response.assert_called_once()
            mock_cache.cache_response.assert_called_once()


@pytest.mark.asyncio
async def test_cache_hit_scenario():
    """Test cache hit scenario."""
    service = CachedTranslationService()
    
    request = TranslationRequest(
        content="Hello world",
        source_language="en", 
        target_language="ar"
    )
    
    # Mock the cache to return a cached response
    with patch('app.services.ai_response_cache.get_cache') as mock_get_cache:
        mock_cache = AsyncMock()
        mock_cache.get_cached_response.return_value = 'مرحبا بالعالم (cached)'
        mock_get_cache.return_value = mock_cache
        
        response = await service.translate_with_cache(request)
        
        assert response.translated_content == 'مرحبا بالعالم (cached)'
        assert response.provider == 'openai'  # Should use first provider
        mock_cache.get_cached_response.assert_called_once()
        # Should not call cache_response since it was a hit
        mock_cache.cache_response.assert_not_called()
