"""
Field Mapping Cache Service

Provides Redis-based caching for field mapping operations to improve performance
and reduce database load. Integrates with the existing AI response cache system.
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import settings
from app.services.ai_response_cache import get_cache

logger = logging.getLogger(__name__)


class FieldMappingCache:
    """
    Redis-based caching service for field mapping operations.
    """
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize the field mapping cache."""
        self.redis = redis_client or redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        self.version = 1
        
        # TTL settings
        self.config_ttl = 1800  # 30 minutes for field configurations
        self.extraction_ttl = 600  # 10 minutes for field extraction results
        self.validation_ttl = 3600  # 1 hour for validation results
        self.stats_ttl = 86400  # 24 hours for stats
        
        # Performance settings
        self.max_content_size = 50000  # Don't cache extractions from very large content
        self.batch_pipeline_size = 100  # Redis pipeline batch size
        
    def _generate_config_key(self, client_id: str, collection_name: str) -> str:
        """Generate cache key for field configuration."""
        return f"field_config:v{self.version}:{client_id}:{collection_name}"
    
    def _generate_extraction_key(self, content: Dict[str, Any], config_hash: str, 
                                language: str = None) -> str:
        """Generate cache key for field extraction results."""
        # Create content hash for reasonably sized content
        content_str = json.dumps(content, sort_keys=True)[:self.max_content_size]
        content_hash = hashlib.md5(content_str.encode()).hexdigest()
        
        lang_suffix = f":{language}" if language else ""
        return f"field_extraction:v{self.version}:{config_hash}:{content_hash}{lang_suffix}"
    
    def _generate_validation_key(self, client_id: str, collection_name: str, 
                                field_paths: List[str]) -> str:
        """Generate cache key for field path validation."""
        paths_hash = hashlib.md5(json.dumps(field_paths, sort_keys=True).encode()).hexdigest()
        return f"field_validation:v{self.version}:{client_id}:{collection_name}:{paths_hash}"
    
    def _generate_config_hash(self, field_config: Dict[str, Any]) -> str:
        """Generate hash for field configuration to track changes."""
        config_str = json.dumps(field_config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    async def get_field_config(self, client_id: str, collection_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached field configuration."""
        try:
            key = self._generate_config_key(client_id, collection_name)
            cached = await self.redis.get(key)
            
            if cached:
                # Track cache hit
                await self.redis.incr(f"field_cache_stats:config:hits")
                
                config_data = json.loads(cached)
                # Update last accessed time
                config_data['_cache_accessed_at'] = time.time()
                await self.redis.set(key, json.dumps(config_data), ex=self.config_ttl)
                
                return config_data
            
            # Track cache miss
            await self.redis.incr(f"field_cache_stats:config:misses")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached field config: {e}")
            return None
    
    async def cache_field_config(self, client_id: str, collection_name: str, 
                                field_config: Dict[str, Any]) -> bool:
        """Cache field configuration with metadata."""
        try:
            key = self._generate_config_key(client_id, collection_name)
            
            # Add cache metadata
            cache_data = {
                **field_config,
                '_cache_stored_at': time.time(),
                '_cache_version': self.version,
                '_config_hash': self._generate_config_hash(field_config)
            }
            
            await self.redis.set(key, json.dumps(cache_data), ex=self.config_ttl)
            logger.debug(f"Cached field config for {client_id}:{collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching field config: {e}")
            return False
    
    async def get_extraction_result(self, content: Dict[str, Any], field_config: Dict[str, Any],
                                  language: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached field extraction result."""
        try:
            config_hash = self._generate_config_hash(field_config)
            key = self._generate_extraction_key(content, config_hash, language)
            
            cached = await self.redis.get(key)
            if cached:
                # Track cache hit
                await self.redis.incr(f"field_cache_stats:extraction:hits")
                
                result = json.loads(cached)
                # Verify the result is still valid for this config
                if result.get('_config_hash') == config_hash:
                    return result.get('extraction_result')
            
            # Track cache miss
            await self.redis.incr(f"field_cache_stats:extraction:misses")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached extraction result: {e}")
            return None
    
    async def cache_extraction_result(self, content: Dict[str, Any], field_config: Dict[str, Any],
                                    extraction_result: Dict[str, Any], language: str = None,
                                    processing_time_ms: int = 0) -> bool:
        """Cache field extraction result."""
        try:
            # Don't cache very large content extractions
            content_size = len(json.dumps(content))
            if content_size > self.max_content_size:
                logger.debug(f"Skipping cache for large content ({content_size} bytes)")
                return False
            
            config_hash = self._generate_config_hash(field_config)
            key = self._generate_extraction_key(content, config_hash, language)
            
            cache_data = {
                'extraction_result': extraction_result,
                '_config_hash': config_hash,
                '_cached_at': time.time(),
                '_processing_time_ms': processing_time_ms,
                '_content_size': content_size,
                '_language': language
            }
            
            await self.redis.set(key, json.dumps(cache_data), ex=self.extraction_ttl)
            logger.debug(f"Cached extraction result for config hash {config_hash[:8]}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching extraction result: {e}")
            return False
    
    async def get_validation_result(self, client_id: str, collection_name: str,
                                  field_paths: List[str]) -> Optional[Dict[str, Any]]:
        """Retrieve cached field path validation result."""
        try:
            key = self._generate_validation_key(client_id, collection_name, field_paths)
            cached = await self.redis.get(key)
            
            if cached:
                # Track cache hit
                await self.redis.incr(f"field_cache_stats:validation:hits")
                return json.loads(cached)
            
            # Track cache miss
            await self.redis.incr(f"field_cache_stats:validation:misses")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached validation result: {e}")
            return None
    
    async def cache_validation_result(self, client_id: str, collection_name: str,
                                    field_paths: List[str], validation_result: Dict[str, Any]) -> bool:
        """Cache field path validation result."""
        try:
            key = self._generate_validation_key(client_id, collection_name, field_paths)
            
            cache_data = {
                'validation_result': validation_result,
                '_cached_at': time.time(),
                '_field_count': len(field_paths)
            }
            
            await self.redis.set(key, json.dumps(cache_data), ex=self.validation_ttl)
            logger.debug(f"Cached validation result for {len(field_paths)} field paths")
            return True
            
        except Exception as e:
            logger.error(f"Error caching validation result: {e}")
            return False
    
    async def invalidate_client_cache(self, client_id: str, collection_name: str = None) -> int:
        """Invalidate all cached data for a client and optionally specific collection."""
        try:
            deleted_count = 0
            
            if collection_name:
                # Invalidate specific collection
                patterns = [
                    f"field_config:v{self.version}:{client_id}:{collection_name}",
                    f"field_validation:v{self.version}:{client_id}:{collection_name}:*"
                ]
            else:
                # Invalidate all client data
                patterns = [
                    f"field_config:v{self.version}:{client_id}:*",
                    f"field_validation:v{self.version}:{client_id}:*"
                ]
            
            for pattern in patterns:
                keys = []
                async for key in self.redis.scan_iter(match=pattern):
                    keys.append(key)
                
                if keys:
                    deleted = await self.redis.delete(*keys)
                    deleted_count += deleted
            
            logger.info(f"Invalidated {deleted_count} cache entries for client {client_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error invalidating client cache: {e}")
            return 0
    
    async def invalidate_extraction_cache(self, config_hash: str = None) -> int:
        """Invalidate extraction cache, optionally for specific config."""
        try:
            if config_hash:
                pattern = f"field_extraction:v{self.version}:{config_hash}:*"
            else:
                pattern = f"field_extraction:v{self.version}:*"
            
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Invalidated {deleted} extraction cache entries")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Error invalidating extraction cache: {e}")
            return 0
    
    async def batch_cache_configs(self, configs: List[Dict[str, Any]]) -> int:
        """Cache multiple field configurations using pipeline for efficiency."""
        if not configs:
            return 0
        
        try:
            pipeline = self.redis.pipeline()
            cached_count = 0
            
            for config_data in configs:
                try:
                    client_id = config_data['client_id']
                    collection_name = config_data['collection_name']
                    field_config = {k: v for k, v in config_data.items() 
                                  if k not in ['client_id', 'collection_name']}
                    
                    key = self._generate_config_key(client_id, collection_name)
                    cache_data = {
                        **field_config,
                        '_cache_stored_at': time.time(),
                        '_cache_version': self.version,
                        '_config_hash': self._generate_config_hash(field_config)
                    }
                    
                    pipeline.set(key, json.dumps(cache_data), ex=self.config_ttl)
                    cached_count += 1
                    
                    # Execute pipeline in batches
                    if cached_count % self.batch_pipeline_size == 0:
                        await pipeline.execute()
                        pipeline = self.redis.pipeline()
                        
                except KeyError as e:
                    logger.warning(f"Missing required key in config: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error preparing config for batch cache: {e}")
                    continue
            
            # Execute remaining items
            if cached_count % self.batch_pipeline_size != 0:
                await pipeline.execute()
            
            logger.info(f"Batch cached {cached_count} field configurations")
            return cached_count
            
        except Exception as e:
            logger.error(f"Error in batch caching configs: {e}")
            return 0
    
    async def warm_cache(self, client_configs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Warm cache with frequently used configurations."""
        result = {
            'configs_cached': 0,
            'errors': 0
        }
        
        for config in client_configs:
            try:
                success = await self.cache_field_config(
                    config['client_id'],
                    config['collection_name'],
                    config.get('field_config', {})
                )
                if success:
                    result['configs_cached'] += 1
                else:
                    result['errors'] += 1
                    
            except Exception as e:
                logger.warning(f"Error warming cache for config: {e}")
                result['errors'] += 1
        
        logger.info(f"Cache warming completed: {result}")
        return result
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        try:
            stats = {
                'field_mapping_cache': {
                    'configs': {'hits': 0, 'misses': 0},
                    'extractions': {'hits': 0, 'misses': 0},
                    'validations': {'hits': 0, 'misses': 0}
                },
                'key_counts': {},
                'memory_info': {},
                'performance': {}
            }
            
            # Get hit/miss stats
            for cache_type in ['config', 'extraction', 'validation']:
                hits = int(await self.redis.get(f"field_cache_stats:{cache_type}:hits") or 0)
                misses = int(await self.redis.get(f"field_cache_stats:{cache_type}:misses") or 0)
                total = hits + misses
                
                stats['field_mapping_cache'][f"{cache_type}s"] = {
                    'hits': hits,
                    'misses': misses,
                    'total': total,
                    'hit_rate': round(hits / total if total > 0 else 0, 3)
                }
            
            # Count keys by type
            key_patterns = {
                'field_configs': f"field_config:v{self.version}:*",
                'field_extractions': f"field_extraction:v{self.version}:*",
                'field_validations': f"field_validation:v{self.version}:*",
                'cache_stats': "field_cache_stats:*"
            }
            
            for key_type, pattern in key_patterns.items():
                count = 0
                async for key in self.redis.scan_iter(match=pattern):
                    count += 1
                stats['key_counts'][key_type] = count
            
            # Get Redis memory info
            try:
                info = await self.redis.info('memory')
                stats['memory_info'] = {
                    'used_memory_human': info.get('used_memory_human'),
                    'used_memory_peak_human': info.get('used_memory_peak_human'),
                    'used_memory_rss_human': info.get('used_memory_rss_human')
                }
            except Exception as e:
                logger.warning(f"Could not get memory info: {e}")
            
            # Performance metrics
            total_requests = sum(
                stats['field_mapping_cache'][cache_type]['total'] 
                for cache_type in ['configs', 'extractions', 'validations']
            )
            total_hits = sum(
                stats['field_mapping_cache'][cache_type]['hits'] 
                for cache_type in ['configs', 'extractions', 'validations']
            )
            
            stats['performance'] = {
                'total_field_requests': total_requests,
                'total_cache_hits': total_hits,
                'overall_hit_rate': round(total_hits / total_requests if total_requests > 0 else 0, 3),
                'ttl_settings': {
                    'config_ttl': self.config_ttl,
                    'extraction_ttl': self.extraction_ttl,
                    'validation_ttl': self.validation_ttl
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
    
    async def cleanup_expired_stats(self) -> int:
        """Clean up old statistics keys."""
        try:
            # Reset very old stats (older than 30 days)
            cutoff_time = time.time() - (30 * 24 * 3600)
            
            # We can't easily determine age of stats keys, so we'll just reset them periodically
            # This could be enhanced with timestamped stats keys
            stats_keys = []
            async for key in self.redis.scan_iter(match="field_cache_stats:*"):
                stats_keys.append(key)
            
            if stats_keys:
                deleted = await self.redis.delete(*stats_keys)
                logger.info(f"Reset {deleted} old cache statistics")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning up expired stats: {e}")
            return 0
    
    async def clear_all_field_cache(self) -> int:
        """Clear all field mapping cache data (emergency use only)."""
        try:
            patterns = [
                f"field_config:v{self.version}:*",
                f"field_extraction:v{self.version}:*",
                f"field_validation:v{self.version}:*",
                "field_cache_stats:*"
            ]
            
            total_deleted = 0
            for pattern in patterns:
                keys = []
                async for key in self.redis.scan_iter(match=pattern):
                    keys.append(key)
                
                if keys:
                    deleted = await self.redis.delete(*keys)
                    total_deleted += deleted
            
            logger.warning(f"Cleared all field mapping cache data: {total_deleted} keys deleted")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Error clearing field cache: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()


# Global field mapping cache instance
_field_cache_instance: Optional[FieldMappingCache] = None


async def get_field_cache() -> FieldMappingCache:
    """Get global field mapping cache instance (singleton pattern)."""
    global _field_cache_instance
    if _field_cache_instance is None:
        _field_cache_instance = FieldMappingCache()
    return _field_cache_instance


async def close_field_cache():
    """Close global field mapping cache instance."""
    global _field_cache_instance
    if _field_cache_instance:
        await _field_cache_instance.close()
        _field_cache_instance = None
