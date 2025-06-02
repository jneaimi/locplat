"""
Unit tests for AI Response Cache

Tests the caching functionality including cache key generation, TTL calculation, 
hit/miss tracking, compression, and provider-specific behavior.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import zlib

from app.services.ai_response_cache import AIResponseCache


class TestAIResponseCache:
    
    @pytest.fixture
    def cache(self):
        """Create a cache instance with mocked Redis."""
        mock_redis = AsyncMock()
        return AIResponseCache(redis_client=mock_redis)
    
    def test_generate_key(self, cache):
        """Test cache key generation."""
        key = cache._generate_key(
            prompt="Hello world",
            provider="openai", 
            model="gpt-3.5-turbo",
            target_language="ar"
        )
        
        assert "ai_response:v1:openai:gpt-3.5-turbo:ar:" in key
        assert len(key.split(":")) == 6  # version:provider:model:lang:hash
    
    def test_generate_key_with_collection(self, cache):
        """Test cache key generation with collection."""
        key = cache._generate_key(
            prompt="Hello world",
            provider="openai",
            model="gpt-3.5-turbo", 
            collection="articles",
            target_language="ar"
        )
        
        assert "collection:articles" in key
    
    def test_calculate_ttl_cost_tiers(self, cache):
        """Test TTL calculation based on provider cost tiers."""
        # Test very high cost tier (Claude Opus)
        ttl_opus = cache._calculate_ttl("standard", "anthropic", "claude-3-opus")
        
        # Test low cost tier (GPT-3.5)
        ttl_gpt35 = cache._calculate_ttl("standard", "openai", "gpt-3.5-turbo")
        
        # Opus should have longer TTL due to higher cost
        assert ttl_opus > ttl_gpt35
    
    def test_calculate_ttl_content_types(self, cache):
        """Test TTL calculation for different content types."""
        base_ttl = cache._calculate_ttl("standard", "openai", "gpt-3.5-turbo")
        critical_ttl = cache._calculate_ttl("critical", "openai", "gpt-3.5-turbo")
        static_ttl = cache._calculate_ttl("static", "openai", "gpt-3.5-turbo")
        
        # Critical should be shorter, static should be longer
        assert critical_ttl < base_ttl < static_ttl
    
    def test_compression(self, cache):
        """Test content compression and decompression."""
        large_content = "x" * 2000  # Larger than compression threshold
        
        compressed = cache._compress_content(large_content)
        decompressed = cache._decompress_content(compressed)
        
        assert isinstance(compressed, bytes)
        assert len(compressed) < len(large_content)  # Should be compressed
        assert decompressed == large_content
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, cache):
        """Test cache hit scenario."""
        # Mock Redis to return cached content
        cache.redis.get.return_value = "مرحبا بالعالم"
        cache.redis.incr = AsyncMock()
        
        result = await cache.get_cached_response(
            prompt="Hello world",
            provider="openai",
            model="gpt-3.5-turbo"
        )
        
        assert result == "مرحبا بالعالم"
        # Should increment hit counter
        cache.redis.incr.assert_called_with('cache_stats:openai:gpt-3.5-turbo:hits')
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss scenario."""
        # Mock Redis to return None (cache miss)
        cache.redis.get.return_value = None
        cache.redis.incr = AsyncMock()
        
        result = await cache.get_cached_response(
            prompt="Hello world",
            provider="openai",
            model="gpt-3.5-turbo"
        )
        
        assert result is None
        # Should increment miss counter
        cache.redis.incr.assert_called_with('cache_stats:openai:gpt-3.5-turbo:misses')