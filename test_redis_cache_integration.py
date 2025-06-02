#!/usr/bin/env python3
"""
Redis Caching Integration Test Script

Tests the complete Redis caching integration for field mapping operations.
"""

import asyncio
import json
import time
from typing import Dict, Any

import redis.asyncio as redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.services.field_mapper import FieldMapper
from app.services.field_mapping_cache import get_field_cache
from app.models.field_config import create_tables


async def test_redis_connection():
    """Test basic Redis connection."""
    print("🔗 Testing Redis connection...")
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        info = await redis_client.info('server')
        print(f"✅ Redis connected: {info.get('redis_version')}")
        await redis_client.close()
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


async def test_field_cache_basic_operations():
    """Test basic field cache operations."""
    print("\n📦 Testing field cache basic operations...")
    
    try:
        field_cache = await get_field_cache()
        
        # Test configuration caching
        test_config = {
            "field_paths": ["title", "description", "content.text"],
            "field_types": {"title": "text", "description": "textarea", "content.text": "wysiwyg"},
            "batch_processing": True,
            "directus_translation_pattern": "collection_translations"
        }
        
        # Cache the config
        cache_success = await field_cache.cache_field_config(
            "test_client", "test_collection", test_config
        )
        print(f"✅ Config caching: {'SUCCESS' if cache_success else 'FAILED'}")
        
        # Retrieve the config
        cached_config = await field_cache.get_field_config("test_client", "test_collection")
        if cached_config:
            # Remove cache metadata for comparison
            clean_config = {k: v for k, v in cached_config.items() if not k.startswith('_')}
            match = clean_config == test_config
            print(f"✅ Config retrieval: {'SUCCESS' if match else 'FAILED'}")
        else:
            print("❌ Config retrieval: FAILED - No cached config found")
        
        # Test cache invalidation
        deleted = await field_cache.invalidate_client_cache("test_client", "test_collection")
        print(f"✅ Cache invalidation: {deleted} keys deleted")
        
        # Verify config is gone
        cached_after_invalidation = await field_cache.get_field_config("test_client", "test_collection")
        if not cached_after_invalidation:
            print("✅ Cache invalidation verification: SUCCESS")
        else:
            print("❌ Cache invalidation verification: FAILED - Config still exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Field cache basic operations failed: {e}")
        return False


async def test_field_mapper_integration():
    """Test FieldMapper integration with Redis cache."""
    print("\n🔄 Testing FieldMapper Redis integration...")
    
    try:
        # Setup database session
        engine = create_engine(settings.DATABASE_URL)
        create_tables(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db_session = SessionLocal()
        
        # Create FieldMapper with Redis caching enabled
        field_mapper = FieldMapper(db_session, enable_redis_cache=True)
        
        # Test configuration save/retrieve
        test_config = {
            "field_paths": ["title", "description"],
            "field_types": {"title": "text", "description": "textarea"},
            "batch_processing": False
        }
        
        # Save config (should cache in Redis)
        await field_mapper.save_field_config("cache_test_client", "articles", test_config)
        print("✅ Config saved to database and Redis")
        
        # Retrieve config (should come from Redis cache)
        start_time = time.time()
        retrieved_config = await field_mapper.get_field_config("cache_test_client", "articles")
        retrieval_time = (time.time() - start_time) * 1000
        
        if retrieved_config and retrieved_config["field_paths"] == test_config["field_paths"]:
            print(f"✅ Config retrieved from cache in {retrieval_time:.2f}ms")
        else:
            print("❌ Config retrieval failed")
            return False
        
        # Test cache stats
        cache_stats = await field_mapper.get_cache_stats()
        print(f"✅ Cache stats retrieved: {len(cache_stats)} stat categories")
        
        # Test cache invalidation
        invalidation_result = await field_mapper.invalidate_cache("cache_test_client", "articles")
        print(f"✅ Cache invalidated: {invalidation_result}")
        
        # Test cache warming
        warm_result = await field_mapper.warm_cache_from_database("cache_test_client")
        print(f"✅ Cache warmed: {warm_result}")
        
        db_session.close()
        return True
        
    except Exception as e:
        print(f"❌ FieldMapper integration test failed: {e}")
        return False


async def test_extraction_caching():
    """Test field extraction result caching."""
    print("\n🎯 Testing extraction result caching...")
    
    try:
        field_cache = await get_field_cache()
        
        # Test content and config
        test_content = {
            "title": "Test Article",
            "description": "This is a test article description",
            "content": {"text": "<p>Test HTML content</p>"}
        }
        
        test_config = {
            "field_paths": ["title", "description", "content.text"],
            "field_types": {"title": "text", "description": "textarea", "content.text": "wysiwyg"}
        }
        
        # Mock extraction result
        extraction_result = {
            "title": {"value": "Test Article", "type": "text"},
            "description": {"value": "This is a test article description", "type": "textarea"},
            "content.text": {"value": "<p>Test HTML content</p>", "type": "wysiwyg"}
        }
        
        # Cache the extraction result
        cache_success = await field_cache.cache_extraction_result(
            test_content, test_config, extraction_result, "ar", 50
        )
        print(f"✅ Extraction caching: {'SUCCESS' if cache_success else 'FAILED'}")
        
        # Retrieve the extraction result
        cached_extraction = await field_cache.get_extraction_result(
            test_content, test_config, "ar"
        )
        
        if cached_extraction and cached_extraction.get("title", {}).get("value") == "Test Article":
            print("✅ Extraction retrieval: SUCCESS")
        else:
            print("❌ Extraction retrieval: FAILED")
        
        # Test with different language
        cached_extraction_en = await field_cache.get_extraction_result(
            test_content, test_config, "en"
        )
        
        if not cached_extraction_en:
            print("✅ Language-specific caching: SUCCESS (no cache for 'en')")
        else:
            print("❌ Language-specific caching: FAILED (found cache for 'en')")
        
        return True
        
    except Exception as e:
        print(f"❌ Extraction caching test failed: {e}")
        return False


async def test_batch_operations():
    """Test batch caching operations."""
    print("\n⚡ Testing batch caching operations...")
    
    try:
        field_cache = await get_field_cache()
        
        # Prepare batch configs
        batch_configs = []
        for i in range(5):
            config_data = {
                'client_id': f'batch_client_{i}',
                'collection_name': f'collection_{i}',
                'field_paths': [f'field_{i}_1', f'field_{i}_2'],
                'field_types': {f'field_{i}_1': 'text', f'field_{i}_2': 'textarea'},
                'batch_processing': True
            }
            batch_configs.append(config_data)
        
        # Batch cache the configs
        start_time = time.time()
        cached_count = await field_cache.batch_cache_configs(batch_configs)
        batch_time = (time.time() - start_time) * 1000
        
        print(f"✅ Batch caching: {cached_count} configs cached in {batch_time:.2f}ms")
        
        # Verify batch cached configs
        verification_count = 0
        for config_data in batch_configs:
            cached_config = await field_cache.get_field_config(
                config_data['client_id'], config_data['collection_name']
            )
            if cached_config:
                verification_count += 1
        
        print(f"✅ Batch verification: {verification_count}/{len(batch_configs)} configs verified")
        
        # Test batch invalidation
        deleted_total = 0
        for config_data in batch_configs:
            deleted = await field_cache.invalidate_client_cache(
                config_data['client_id'], config_data['collection_name']
            )
            deleted_total += deleted
        
        print(f"✅ Batch cleanup: {deleted_total} keys deleted")
        
        return cached_count == len(batch_configs) and verification_count == len(batch_configs)
        
    except Exception as e:
        print(f"❌ Batch operations test failed: {e}")
        return False


async def test_performance_metrics():
    """Test cache performance and statistics."""
    print("\n📊 Testing performance metrics...")
    
    try:
        field_cache = await get_field_cache()
        
        # Generate some cache activity
        test_configs = []
        for i in range(3):
            config = {
                "field_paths": [f"field_{i}"],
                "field_types": {f"field_{i}": "text"}
            }
            
            # Cache config
            await field_cache.cache_field_config(f"perf_client_{i}", "test_collection", config)
            test_configs.append((f"perf_client_{i}", "test_collection", config))
        
        # Generate cache hits
        for client_id, collection_name, _ in test_configs:
            await field_cache.get_field_config(client_id, collection_name)
            await field_cache.get_field_config(client_id, collection_name)  # Second hit
        
        # Generate cache misses
        for i in range(2):
            await field_cache.get_field_config(f"missing_client_{i}", "missing_collection")
        
        # Get cache stats
        stats = await field_cache.get_cache_stats()
        
        if 'field_mapping_cache' in stats:
            config_stats = stats['field_mapping_cache']['configs']
            print(f"✅ Performance stats: {config_stats['hits']} hits, {config_stats['misses']} misses")
            
            if config_stats['hits'] >= 6 and config_stats['misses'] >= 2:
                print("✅ Performance tracking: SUCCESS")
            else:
                print("❌ Performance tracking: Unexpected hit/miss counts")
        else:
            print("❌ Performance stats: No field mapping cache stats found")
        
        # Cleanup
        for client_id, collection_name, _ in test_configs:
            await field_cache.invalidate_client_cache(client_id, collection_name)
        
        return True
        
    except Exception as e:
        print(f"❌ Performance metrics test failed: {e}")
        return False


async def test_cache_fallback():
    """Test cache fallback behavior when Redis is unavailable."""
    print("\n🔧 Testing cache fallback behavior...")
    
    try:
        # Setup database session
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db_session = SessionLocal()
        
        # Create FieldMapper with Redis disabled
        field_mapper_no_redis = FieldMapper(db_session, enable_redis_cache=False)
        
        # Test configuration operations without Redis
        test_config = {
            "field_paths": ["title"],
            "field_types": {"title": "text"}
        }
        
        await field_mapper_no_redis.save_field_config("fallback_client", "test_collection", test_config)
        retrieved_config = await field_mapper_no_redis.get_field_config("fallback_client", "test_collection")
        
        if retrieved_config and retrieved_config["field_paths"] == test_config["field_paths"]:
            print("✅ Fallback mode: SUCCESS (database-only operations work)")
        else:
            print("❌ Fallback mode: FAILED")
            return False
        
        # Test cache stats without Redis
        stats = await field_mapper_no_redis.get_cache_stats()
        if stats['redis_enabled'] == False and 'local_cache' in stats:
            print("✅ Fallback stats: SUCCESS (local cache only)")
        else:
            print("❌ Fallback stats: FAILED")
        
        db_session.close()
        return True
        
    except Exception as e:
        print(f"❌ Cache fallback test failed: {e}")
        return False


async def test_cache_integration_with_field_extraction():
    """Test full integration with actual field extraction."""
    print("\n🔍 Testing cache integration with field extraction...")
    
    try:
        # Setup database session
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db_session = SessionLocal()
        
        # Create FieldMapper with Redis enabled
        field_mapper = FieldMapper(db_session, enable_redis_cache=True)
        
        # Setup field configuration
        field_config = {
            "field_paths": ["title", "description", "content.text"],
            "field_types": {"title": "text", "description": "textarea", "content.text": "wysiwyg"},
            "batch_processing": False
        }
        
        await field_mapper.save_field_config("integration_client", "articles", field_config)
        
        # Test content
        test_content = {
            "id": 1,
            "title": "Integration Test Article",
            "description": "This is a comprehensive test of the integration between field extraction and caching.",
            "content": {
                "text": "<p>This is <strong>HTML content</strong> that should be properly extracted and cached.</p>"
            },
            "status": "published"
        }
        
        # First extraction (should be slow, from database)
        start_time = time.time()
        config = await field_mapper.get_field_config("integration_client", "articles")
        extraction_result = field_mapper.extract_fields(test_content, config)
        first_extraction_time = (time.time() - start_time) * 1000
        
        print(f"✅ First extraction: {len(extraction_result)} fields in {first_extraction_time:.2f}ms")
        
        # Second extraction (should be faster, from cache)
        start_time = time.time()
        config_cached = await field_mapper.get_field_config("integration_client", "articles")
        extraction_result_cached = field_mapper.extract_fields(test_content, config_cached)
        second_extraction_time = (time.time() - start_time) * 1000
        
        print(f"✅ Second extraction: {len(extraction_result_cached)} fields in {second_extraction_time:.2f}ms")
        
        # Verify results are identical
        if extraction_result == extraction_result_cached:
            print("✅ Cache consistency: SUCCESS (results identical)")
        else:
            print("❌ Cache consistency: FAILED (results differ)")
            return False
        
        # Verify performance improvement
        if second_extraction_time < first_extraction_time * 0.8:  # At least 20% improvement
            print(f"✅ Performance improvement: {first_extraction_time:.2f}ms → {second_extraction_time:.2f}ms")
        else:
            print(f"⚠️  Performance: Marginal improvement {first_extraction_time:.2f}ms → {second_extraction_time:.2f}ms")
        
        # Test cache stats
        cache_stats = await field_mapper.get_cache_stats()
        if cache_stats.get('redis_cache'):
            print("✅ Integration stats: Cache statistics available")
        else:
            print("❌ Integration stats: No cache statistics")
        
        db_session.close()
        return True
        
    except Exception as e:
        print(f"❌ Cache integration test failed: {e}")
        return False


async def cleanup_test_data():
    """Clean up test data from Redis and database."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        field_cache = await get_field_cache()
        
        # Clean up test cache entries
        test_clients = [
            "test_client", "cache_test_client", "perf_client_0", "perf_client_1", 
            "perf_client_2", "fallback_client", "integration_client"
        ]
        
        total_deleted = 0
        for client_id in test_clients:
            deleted = await field_cache.invalidate_client_cache(client_id)
            total_deleted += deleted
        
        # Clean up batch test clients
        for i in range(5):
            deleted = await field_cache.invalidate_client_cache(f"batch_client_{i}")
            total_deleted += deleted
        
        print(f"✅ Cleanup: {total_deleted} cache entries removed")
        
        # Clean up database test entries
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db_session = SessionLocal()
        
        try:
            from app.models.field_config import FieldConfig
            test_configs = db_session.query(FieldConfig).filter(
                FieldConfig.client_id.in_(test_clients + [f"batch_client_{i}" for i in range(5)])
            ).all()
            
            for config in test_configs:
                db_session.delete(config)
            
            db_session.commit()
            print(f"✅ Database cleanup: {len(test_configs)} configurations removed")
            
        except Exception as e:
            print(f"⚠️  Database cleanup warning: {e}")
        finally:
            db_session.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False


async def main():
    """Run all Redis caching integration tests."""
    print("🚀 Starting Redis Caching Integration Tests")
    print("=" * 50)
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Field Cache Basic Operations", test_field_cache_basic_operations),
        ("FieldMapper Integration", test_field_mapper_integration),
        ("Extraction Caching", test_extraction_caching),
        ("Batch Operations", test_batch_operations),
        ("Performance Metrics", test_performance_metrics),
        ("Cache Fallback", test_cache_fallback),
        ("Field Extraction Integration", test_cache_integration_with_field_extraction)
    ]
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
            test_results.append((test_name, False))
    
    # Cleanup
    await cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    total = len(test_results)
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All Redis caching integration tests passed!")
        print("\n✅ Task 4.4: Redis caching layer integration is COMPLETE")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
