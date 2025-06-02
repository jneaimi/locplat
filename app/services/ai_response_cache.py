"""
AI Response Cache Service

Implements intelligent caching for AI translation responses across multiple providers
(OpenAI, Anthropic, Mistral, DeepSeek) with cost-aware TTL strategies.
"""

import asyncio
import hashlib
import json
import logging
import zlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)


class AIResponseCache:
    """
    Intelligent caching layer for AI translation responses with provider-specific optimizations.
    """

    def __init__(self, redis_client: Optional[Redis] = None, default_ttl_seconds: int = 86400):
        """Initialize the AI response cache."""
        self.redis = redis_client or redis.from_url(
            settings.REDIS_URL, 
            encoding="utf-8", 
            decode_responses=False  # We handle encoding manually for compression
        )
        self.default_ttl = default_ttl_seconds
        self.version = 1  # For cache versioning
        
        # Compression threshold (compress responses larger than 1KB)
        self.compression_threshold = 1000        
        # Define cost tiers for different providers to influence caching strategy
        self.provider_cost_tiers = {
            'openai': {
                'gpt-3.5-turbo': 'low',
                'gpt-4': 'high',
                'gpt-4-turbo': 'high',
                'gpt-4o': 'high',
                'gpt-4o-mini': 'medium'
            },
            'anthropic': {
                'claude-instant': 'medium',
                'claude-2': 'high', 
                'claude-3-opus': 'very_high',
                'claude-3-sonnet': 'high',
                'claude-3-haiku': 'medium',
                'claude-3-5-sonnet': 'high',
                'claude-3-5-haiku': 'medium'
            },
            'mistral': {
                'mistral-tiny': 'low',
                'mistral-small': 'medium',
                'mistral-medium': 'medium',
                'mistral-large': 'high',
                'mistral-7b-instruct': 'low',
                'mixtral-8x7b-instruct': 'medium'
            },
            'deepseek': {
                'deepseek-coder': 'medium',
                'deepseek-chat': 'medium',
                'deepseek-v2': 'medium'
            }
        }

    def _generate_key(
        self, 
        prompt: str, 
        provider: str, 
        model: str, 
        collection: Optional[str] = None,
        target_language: str = "ar"
    ) -> str:
        """Generate a unique cache key based on content and parameters."""
        # Create content hash including target language for uniqueness
        content_data = f"{prompt}:{target_language}"
        content_hash = hashlib.md5(content_data.encode()).hexdigest()
        
        base_key = f"ai_response:v{self.version}:{provider}:{model}:{target_language}:{content_hash}"
        
        if collection:
            return f"{base_key}:collection:{collection}"
        return base_key

    def _compress_content(self, content: str) -> bytes:
        """Compress large content blocks using zlib."""
        return zlib.compress(content.encode('utf-8'), level=6)

    def _decompress_content(self, compressed_data: bytes) -> str:
        """Decompress content and return as string."""
        return zlib.decompress(compressed_data).decode('utf-8')

    def _calculate_ttl(
        self, 
        content_type: str, 
        provider: str, 
        model: str, 
        confidence: float = 1.0
    ) -> int:
        """Calculate dynamic TTL based on content type, provider cost tier, and confidence."""
        base_ttl = self.default_ttl
        
        # Adjust TTL based on content type
        content_type_multipliers = {
            'critical': 0.5,    # 12 hours for critical content
            'static': 7.0,      # 7 days for static content  
            'standard': 1.0,    # Default
            'temporary': 0.25   # 6 hours for temporary content
        }
        
        content_factor = content_type_multipliers.get(content_type.lower(), 1.0)
        
        # Adjust TTL based on provider cost tier
        cost_tier = 'medium'  # Default
        if provider in self.provider_cost_tiers and model in self.provider_cost_tiers[provider]:
            cost_tier = self.provider_cost_tiers[provider][model]
        
        # More expensive models get longer cache times to save costs
        tier_multipliers = {
            'low': 0.8,
            'medium': 1.0,
            'high': 1.5,
            'very_high': 2.0
        }
        
        tier_factor = tier_multipliers.get(cost_tier, 1.0)
        confidence_factor = max(0.5, min(1.5, confidence))  # Between 0.5 and 1.5
        
        return int(base_ttl * content_factor * tier_factor * confidence_factor)

    async def get_cached_response(
        self, 
        prompt: str, 
        provider: str, 
        model: str, 
        collection: Optional[str] = None,
        target_language: str = "ar"
    ) -> Optional[str]:
        """Retrieve cached response if available."""
        try:
            key = self._generate_key(prompt, provider, model, collection, target_language)
            cached = await self.redis.get(key)
            
            if cached:
                # Track cache hit for this provider
                await self.redis.incr(f'cache_stats:{provider}:{model}:hits')
                
                # Check if content is compressed
                try:
                    if isinstance(cached, bytes):
                        return self._decompress_content(cached)
                    else:
                        return cached
                except zlib.error:
                    # Not compressed, return as string
                    return cached.decode('utf-8') if isinstance(cached, bytes) else cached
            
            # Track cache miss for this provider
            await self.redis.incr(f'cache_stats:{provider}:{model}:misses')
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached response: {e}")
            return None

    async def cache_response(
        self, 
        prompt: str, 
        provider: str, 
        model: str, 
        response: str, 
        collection: Optional[str] = None,
        target_language: str = "ar",
        content_type: str = 'standard', 
        confidence: float = 1.0
    ) -> bool:
        """Cache AI response with appropriate TTL and compression."""
        try:
            key = self._generate_key(prompt, provider, model, collection, target_language)
            ttl = self._calculate_ttl(content_type, provider, model, confidence)
            
            # Compress large content
            if len(response) > self.compression_threshold:
                compressed_data = self._compress_content(response)
                await self.redis.set(key, compressed_data, ex=ttl)
                logger.debug(f"Cached compressed response ({len(compressed_data)} bytes) for {provider}:{model}")
            else:
                await self.redis.set(key, response, ex=ttl)
                logger.debug(f"Cached response for {provider}:{model}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching response: {e}")
            return False

    async def cache_batch_responses(self, items: List[Dict[str, Any]]) -> int:
        """Cache multiple responses efficiently using pipeline."""
        if not items:
            return 0
            
        try:
            pipeline = self.redis.pipeline()
            cached_count = 0
            
            for item in items:
                try:
                    key = self._generate_key(
                        item['prompt'], 
                        item['provider'], 
                        item['model'],
                        item.get('collection'),
                        item.get('target_language', 'ar')
                    )
                    
                    ttl = self._calculate_ttl(
                        item.get('content_type', 'standard'), 
                        item['provider'], 
                        item['model'],
                        item.get('confidence', 1.0)
                    )
                    
                    response = item['response']
                    
                    # Compress large content
                    if len(response) > self.compression_threshold:
                        compressed_data = self._compress_content(response)
                        pipeline.set(key, compressed_data, ex=ttl)
                    else:
                        pipeline.set(key, response, ex=ttl)
                    
                    cached_count += 1
                    
                except KeyError as e:
                    logger.warning(f"Missing required key in batch item: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error preparing batch item: {e}")
                    continue
            
            # Execute pipeline
            await pipeline.execute()
            logger.info(f"Batch cached {cached_count} responses")
            return cached_count
            
        except Exception as e:
            logger.error(f"Error in batch caching: {e}")
            return 0

    async def invalidate_cache(
        self, 
        provider: Optional[str] = None, 
        model: Optional[str] = None, 
        collection: Optional[str] = None,
        target_language: Optional[str] = None
    ) -> int:
        """Invalidate cached responses based on criteria."""
        try:
            # Build pattern for keys to delete
            pattern_parts = [f'ai_response:v{self.version}']
            
            pattern_parts.append(provider or '*')
            pattern_parts.append(model or '*')
            pattern_parts.append(target_language or '*')
            pattern_parts.append('*')  # For content hash
            
            if collection:
                pattern = ':'.join(pattern_parts) + f':collection:{collection}'
            else:
                pattern = ':'.join(pattern_parts)
            
            # Get keys matching pattern (scan for better performance)
            keys = []
            async for key in self.redis.scan_iter(match=pattern, count=100):
                keys.append(key)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0

    async def warm_cache(self, frequent_content: List[Dict[str, Any]]) -> int:
        """Pre-populate cache with frequently accessed content."""
        warmed_count = 0
        
        for item in frequent_content:
            try:
                cached = await self.get_cached_response(
                    item['prompt'],
                    item['provider'],
                    item['model'],
                    item.get('collection'),
                    item.get('target_language', 'ar')
                )
                
                # If not in cache and we have a response, cache it
                if not cached and 'response' in item:
                    success = await self.cache_response(
                        item['prompt'],
                        item['provider'],
                        item['model'],
                        item['response'],
                        item.get('collection'),
                        item.get('target_language', 'ar'),
                        item.get('content_type', 'standard'),
                        item.get('confidence', 1.0)
                    )
                    if success:
                        warmed_count += 1
                        
            except Exception as e:
                logger.warning(f"Error warming cache item: {e}")
                continue
        
        logger.info(f"Cache warming completed: {warmed_count} items")
        return warmed_count

    async def get_cache_stats(
        self, 
        provider: Optional[str] = None, 
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get cache hit/miss statistics."""
        try:
            if provider and model:
                # Get stats for specific provider/model
                hits_key = f'cache_stats:{provider}:{model}:hits'
                misses_key = f'cache_stats:{provider}:{model}:misses'
                
                hits = int(await self.redis.get(hits_key) or 0)
                misses = int(await self.redis.get(misses_key) or 0)
                
                total = hits + misses
                hit_rate = hits / total if total > 0 else 0
                
                return {
                    'provider': provider,
                    'model': model,
                    'hits': hits,
                    'misses': misses,
                    'total_requests': total,
                    'hit_rate': round(hit_rate, 3)
                }
                
            elif provider:
                # Get stats for all models of a provider
                stats = {
                    'provider': provider, 
                    'models': {}, 
                    'total_hits': 0, 
                    'total_misses': 0
                }
                
                # Scan for all hits keys for this provider
                pattern = f'cache_stats:{provider}:*:hits'
                async for key in self.redis.scan_iter(match=pattern):
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    key_parts = key_str.split(':')
                    if len(key_parts) >= 4:
                        model_name = key_parts[2]
                        
                        hits = int(await self.redis.get(f'cache_stats:{provider}:{model_name}:hits') or 0)
                        misses = int(await self.redis.get(f'cache_stats:{provider}:{model_name}:misses') or 0)
                        total = hits + misses
                        
                        stats['models'][model_name] = {
                            'hits': hits,
                            'misses': misses,
                            'total_requests': total,
                            'hit_rate': round(hits / total if total > 0 else 0, 3)
                        }
                        
                        stats['total_hits'] += hits
                        stats['total_misses'] += misses
                
                total = stats['total_hits'] + stats['total_misses']
                stats['overall_hit_rate'] = round(stats['total_hits'] / total if total > 0 else 0, 3)
                stats['total_requests'] = total
                
                return stats
                
            else:
                # Get stats for all providers - simplified version
                stats = {'providers': {}, 'overall': {'hits': 0, 'misses': 0}}
                
                # Scan for all cache stats
                async for key in self.redis.scan_iter(match='cache_stats:*:*:hits'):
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    key_parts = key_str.split(':')
                    if len(key_parts) >= 4:
                        provider_name = key_parts[1]
                        model_name = key_parts[2]
                        
                        hits = int(await self.redis.get(f'cache_stats:{provider_name}:{model_name}:hits') or 0)
                        misses = int(await self.redis.get(f'cache_stats:{provider_name}:{model_name}:misses') or 0)
                        
                        if provider_name not in stats['providers']:
                            stats['providers'][provider_name] = {
                                'total_hits': 0, 
                                'total_misses': 0
                            }
                        
                        stats['providers'][provider_name]['total_hits'] += hits
                        stats['providers'][provider_name]['total_misses'] += misses
                        stats['overall']['hits'] += hits
                        stats['overall']['misses'] += misses
                
                # Calculate hit rates
                for provider_name in stats['providers']:
                    total = stats['providers'][provider_name]['total_hits'] + stats['providers'][provider_name]['total_misses']
                    stats['providers'][provider_name]['total_requests'] = total
                    stats['providers'][provider_name]['hit_rate'] = round(
                        stats['providers'][provider_name]['total_hits'] / total if total > 0 else 0, 3
                    )
                
                total = stats['overall']['hits'] + stats['overall']['misses']
                stats['overall']['total_requests'] = total
                stats['overall']['hit_rate'] = round(stats['overall']['hits'] / total if total > 0 else 0, 3)
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}

    async def get_cache_info(self) -> Dict[str, Any]:
        """Get general cache information including memory usage and key counts."""
        try:
            info = await self.redis.info('memory')
            
            # Count cache keys
            cache_keys = 0
            stats_keys = 0
            
            async for key in self.redis.scan_iter(match=f'ai_response:v{self.version}:*'):
                cache_keys += 1
                
            async for key in self.redis.scan_iter(match='cache_stats:*'):
                stats_keys += 1
            
            return {
                'version': self.version,
                'cache_keys': cache_keys,
                'stats_keys': stats_keys,
                'memory_used': info.get('used_memory_human'),
                'memory_peak': info.get('used_memory_peak_human'),
                'default_ttl': self.default_ttl,
                'compression_threshold': self.compression_threshold,
                'provider_cost_tiers': self.provider_cost_tiers
            }
            
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {'error': str(e)}

    async def clear_all_cache(self) -> int:
        """Clear all cache data (emergency use only)."""
        try:
            # Delete all cache and stats keys
            keys_to_delete = []
            
            async for key in self.redis.scan_iter(match=f'ai_response:v{self.version}:*'):
                keys_to_delete.append(key)
                
            async for key in self.redis.scan_iter(match='cache_stats:*'):
                keys_to_delete.append(key)
            
            if keys_to_delete:
                deleted = await self.redis.delete(*keys_to_delete)
                logger.warning(f"Cleared all cache data: {deleted} keys deleted")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()


# Global cache instance
_cache_instance: Optional[AIResponseCache] = None


async def get_cache() -> AIResponseCache:
    """Get global cache instance (singleton pattern)."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = AIResponseCache()
    return _cache_instance


async def close_cache():
    """Close global cache instance."""
    global _cache_instance
    if _cache_instance:
        await _cache_instance.close()
        _cache_instance = None
