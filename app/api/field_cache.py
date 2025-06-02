"""
Field Mapping Cache Management API

Provides endpoints for managing Redis cache for field mapping operations.
"""

import logging
import time
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.field_mapper import FieldMapper
from app.services.field_mapping_cache import get_field_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/field-cache", tags=["field-cache"])


@router.get("/stats")
async def get_cache_stats(
    client_id: Optional[str] = Query(None, description="Filter stats by client ID"),
    db: Session = Depends(get_db)
):
    """Get comprehensive field mapping cache statistics."""
    try:
        # Get field mapper stats
        field_mapper = FieldMapper(db, enable_redis_cache=True)
        mapper_stats = await field_mapper.get_cache_stats()
        
        # Get field cache stats
        field_cache = await get_field_cache()
        cache_stats = await field_cache.get_cache_stats()
        
        return {
            "status": "success",
            "data": {
                "field_mapper": mapper_stats,
                "redis_cache": cache_stats,
                "timestamp": int(time.time())
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invalidate")
async def invalidate_cache(
    client_id: str = Query(..., description="Client ID to invalidate cache for"),
    collection_name: Optional[str] = Query(None, description="Specific collection to invalidate"),
    db: Session = Depends(get_db)
):
    """Invalidate field mapping cache for a client/collection."""
    try:
        field_mapper = FieldMapper(db, enable_redis_cache=True)
        result = await field_mapper.invalidate_cache(client_id, collection_name)
        
        return {
            "status": "success",
            "message": f"Cache invalidated for client {client_id}" + 
                      (f" collection {collection_name}" if collection_name else ""),
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warm")
async def warm_cache(
    client_id: Optional[str] = Query(None, description="Client ID to warm cache for"),
    db: Session = Depends(get_db)
):
    """Warm field mapping cache from database configurations."""
    try:
        field_mapper = FieldMapper(db, enable_redis_cache=True)
        result = await field_mapper.warm_cache_from_database(client_id)
        
        return {
            "status": "success",
            "message": "Cache warming completed",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error warming cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_cache(
    confirm: bool = Query(False, description="Confirm cache clearing (required)"),
    cache_type: str = Query("field", description="Type of cache to clear: 'field' or 'all'")
):
    """Clear field mapping cache (emergency use only)."""
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Cache clearing requires confirmation. Set confirm=true"
        )
    
    try:
        field_cache = await get_field_cache()
        
        if cache_type == "field":
            deleted = await field_cache.clear_all_field_cache()
            message = f"Cleared field mapping cache: {deleted} keys deleted"
        elif cache_type == "all":
            # Also clear AI response cache if requested
            from app.services.ai_response_cache import get_cache
            ai_cache = await get_cache()
            field_deleted = await field_cache.clear_all_field_cache()
            ai_deleted = await ai_cache.clear_all_cache()
            deleted = field_deleted + ai_deleted
            message = f"Cleared all caches: {deleted} keys deleted"
        else:
            raise HTTPException(status_code=400, detail="Invalid cache_type. Use 'field' or 'all'")
        
        return {
            "status": "success",
            "message": message,
            "data": {"keys_deleted": deleted}
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_cache_info():
    """Get general cache configuration and status information."""
    try:
        field_cache = await get_field_cache()
        
        # Get Redis info
        info = await field_cache.redis.info()
        
        # Get cache key counts
        stats = await field_cache.get_cache_stats()
        
        return {
            "status": "success",
            "data": {
                "redis_info": {
                    "version": info.get("redis_version"),
                    "memory_used": info.get("used_memory_human"),
                    "memory_peak": info.get("used_memory_peak_human"),
                    "connected_clients": info.get("connected_clients"),
                    "uptime_in_seconds": info.get("uptime_in_seconds")
                },
                "cache_config": {
                    "field_config_ttl": field_cache.config_ttl,
                    "extraction_ttl": field_cache.extraction_ttl,
                    "validation_ttl": field_cache.validation_ttl,
                    "max_content_size": field_cache.max_content_size
                },
                "statistics": stats
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-config")
async def validate_cache_configuration():
    """Validate that cache configuration is working properly."""
    try:
        field_cache = await get_field_cache()
        
        # Test basic Redis operations
        test_key = "cache_test:validation"
        test_value = "test_value"
        
        # Test set/get
        await field_cache.redis.set(test_key, test_value, ex=10)
        retrieved = await field_cache.redis.get(test_key)
        
        if retrieved != test_value:
            raise Exception("Cache set/get validation failed")
        
        # Clean up
        await field_cache.redis.delete(test_key)
        
        # Test field cache operations
        test_config = {
            "field_paths": ["test.field"],
            "field_types": {"test.field": "text"}
        }
        
        cache_success = await field_cache.cache_field_config(
            "test_client", "test_collection", test_config
        )
        
        if cache_success:
            cached_config = await field_cache.get_field_config("test_client", "test_collection")
            if not cached_config:
                raise Exception("Field config caching validation failed")
            
            # Clean up
            await field_cache.invalidate_client_cache("test_client", "test_collection")
        
        return {
            "status": "success",
            "message": "Cache configuration validation passed",
            "data": {
                "redis_operations": "OK",
                "field_cache_operations": "OK" if cache_success else "FAILED",
                "timestamp": int(time.time())
            }
        }
        
    except Exception as e:
        logger.error(f"Cache validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cache validation failed: {e}")


@router.get("/performance")
async def get_cache_performance_metrics():
    """Get detailed cache performance metrics."""
    try:
        field_cache = await get_field_cache()
        stats = await field_cache.get_cache_stats()
        
        # Calculate performance metrics
        performance_data = {
            "hit_rates": {},
            "efficiency": {},
            "recommendations": []
        }
        
        # Calculate hit rates for different cache types
        for cache_type in ['configs', 'extractions', 'validations']:
            if cache_type in stats.get('field_mapping_cache', {}):
                cache_stats = stats['field_mapping_cache'][cache_type]
                hit_rate = cache_stats.get('hit_rate', 0)
                performance_data['hit_rates'][cache_type] = hit_rate
                
                # Add recommendations based on hit rates
                if hit_rate < 0.5:
                    performance_data['recommendations'].append(
                        f"Low hit rate for {cache_type} ({hit_rate:.1%}). Consider increasing TTL or warming cache."
                    )
                elif hit_rate > 0.9:
                    performance_data['recommendations'].append(
                        f"Excellent hit rate for {cache_type} ({hit_rate:.1%}). Cache is well-optimized."
                    )
        
        # Calculate overall efficiency
        total_requests = sum(
            stats.get('field_mapping_cache', {}).get(cache_type, {}).get('total', 0)
            for cache_type in ['configs', 'extractions', 'validations']
        )
        total_hits = sum(
            stats.get('field_mapping_cache', {}).get(cache_type, {}).get('hits', 0)
            for cache_type in ['configs', 'extractions', 'validations']
        )
        
        performance_data['efficiency'] = {
            'overall_hit_rate': total_hits / total_requests if total_requests > 0 else 0,
            'total_requests': total_requests,
            'total_cache_hits': total_hits,
            'cache_savings': total_hits  # Each hit saves a database/computation operation
        }
        
        return {
            "status": "success",
            "data": {
                "performance": performance_data,
                "detailed_stats": stats,
                "timestamp": int(time.time())
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
