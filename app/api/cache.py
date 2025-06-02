"""
Cache Management API Endpoints

Provides REST API endpoints for managing the AI response cache.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional

from app.services.ai_response_cache import get_cache

router = APIRouter(prefix="/cache", tags=["cache"])


@router.get("/stats")
async def get_cache_statistics(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    model: Optional[str] = Query(None, description="Filter by model")
) -> Dict[str, Any]:
    """Get cache hit/miss statistics."""
    try:
        cache = await get_cache()
        return await cache.get_cache_stats(provider, model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_cache_info() -> Dict[str, Any]:
    """Get general cache information."""
    try:
        cache = await get_cache()
        return await cache.get_cache_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/invalidate")
async def invalidate_cache(
    provider: Optional[str] = Query(None, description="Provider to invalidate"),
    model: Optional[str] = Query(None, description="Model to invalidate"),
    collection: Optional[str] = Query(None, description="Collection to invalidate"),
    target_language: Optional[str] = Query(None, description="Language to invalidate")
) -> Dict[str, Any]:
    """Invalidate cache entries based on criteria."""
    try:
        cache = await get_cache()
        deleted_count = await cache.invalidate_cache(provider, model, collection, target_language)
        return {
            "deleted_count": deleted_count,
            "message": f"Invalidated {deleted_count} cache entries"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_all_cache() -> Dict[str, Any]:
    """Clear all cache data (emergency use only)."""
    try:
        cache = await get_cache()
        deleted_count = await cache.clear_all_cache()
        return {
            "deleted_count": deleted_count,
            "message": f"Cleared all cache data: {deleted_count} keys deleted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
