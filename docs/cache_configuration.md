# Redis Cache Configuration for LocPlat

## Cache Settings
- **Default TTL**: 24 hours (86400 seconds)
- **Compression Threshold**: 1KB (1000 bytes)
- **Cache Key Version**: v1

## Provider Cost Tiers (affects TTL)
- **Very High**: Claude-3 Opus (2x TTL multiplier)
- **High**: GPT-4, Claude-3 Sonnet, Mistral Large (1.5x TTL)
- **Medium**: Claude-3 Haiku, DeepSeek models (1x TTL)
- **Low**: GPT-3.5-Turbo, Mistral Tiny (0.8x TTL)

## Content Type TTL Multipliers
- **Critical**: 0.5x (12 hours)
- **Standard**: 1x (24 hours) 
- **Static**: 7x (7 days)
- **Temporary**: 0.25x (6 hours)

## Cache Key Format
```
ai_response:v{version}:{provider}:{model}:{language}:{content_hash}[:collection:{collection}]
```

## Statistics Keys
```
cache_stats:{provider}:{model}:hits
cache_stats:{provider}:{model}:misses
```

## API Endpoints
- `GET /api/v1/cache/stats` - Get cache statistics
- `GET /api/v1/cache/info` - Get cache information
- `DELETE /api/v1/cache/invalidate` - Invalidate cache entries
- `DELETE /api/v1/cache/clear` - Clear all cache (emergency)

## Usage Examples

### Get Cache Stats
```bash
curl http://localhost:8000/api/v1/cache/stats
curl http://localhost:8000/api/v1/cache/stats?provider=openai
curl http://localhost:8000/api/v1/cache/stats?provider=anthropic&model=claude-3-opus
```

### Invalidate Cache
```bash
# Invalidate all OpenAI cache
curl -X DELETE http://localhost:8000/api/v1/cache/invalidate?provider=openai

# Invalidate specific collection
curl -X DELETE http://localhost:8000/api/v1/cache/invalidate?collection=articles

# Invalidate Arabic translations
curl -X DELETE http://localhost:8000/api/v1/cache/invalidate?target_language=ar
```
