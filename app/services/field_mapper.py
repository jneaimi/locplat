"""Field Mapper Service for LocPlat Translation Service"""

import json
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from ..models.field_config import FieldConfig, FieldProcessingLog
from ..models.field_types import (
    FieldType, DirectusTranslationPattern, ContentProcessingStrategy,
    is_rtl_language, get_field_type_from_directus
)
from .field_mapping_cache import get_field_cache


class FieldMapper:
    """Main service for handling field mapping and content processing with Redis caching."""
    
    def __init__(self, db_session: Session, enable_logging: bool = True, enable_redis_cache: bool = True):
        self.db_session = db_session
        self.enable_logging = enable_logging
        self.enable_redis_cache = enable_redis_cache
        self._processing_cache = {}  # Local fallback cache
        self._field_cache = None  # Will be initialized when needed
    
    async def _get_field_cache(self):
        """Get field cache instance lazily."""
        if self.enable_redis_cache and self._field_cache is None:
            self._field_cache = await get_field_cache()
        return self._field_cache
    
    async def get_field_config(self, client_id: str, collection_name: str) -> Dict[str, Any]:
        """Retrieve field configuration with Redis caching support."""
        # Try Redis cache first if enabled
        if self.enable_redis_cache:
            try:
                field_cache = await self._get_field_cache()
                cached_config = await field_cache.get_field_config(client_id, collection_name)
                if cached_config:
                    # Remove cache metadata before returning
                    return {k: v for k, v in cached_config.items() if not k.startswith('_')}
            except Exception as e:
                self.log_warning(f"Redis cache error, falling back to local cache: {e}")
        
        # Fallback to local cache and database
        cache_key = f"{client_id}:{collection_name}"
        if cache_key in self._processing_cache:
            cached_config, cache_time = self._processing_cache[cache_key]
            if time.time() - cache_time < 300:  # 5 minute cache
                return cached_config
        
        config = self.db_session.query(FieldConfig).filter_by(
            client_id=client_id, collection_name=collection_name
        ).first()
        
        if not config:
            default_config = {
                "field_paths": [], "field_types": {},
                "is_translation_collection": False, "primary_collection": None,
                "directus_translation_pattern": DirectusTranslationPattern.COLLECTION_TRANSLATIONS.value,
                "rtl_field_mapping": {}, "language_field_overrides": {},
                "batch_processing": False, "preserve_html_structure": True,
                "content_sanitization": True, "custom_transformations": {},
                "validation_rules": {}
            }
            self._processing_cache[cache_key] = (default_config, time.time())
            
            # Cache in Redis if enabled
            if self.enable_redis_cache:
                try:
                    field_cache = await self._get_field_cache()
                    await field_cache.cache_field_config(client_id, collection_name, default_config)
                except Exception as e:
                    self.log_warning(f"Failed to cache default config in Redis: {e}")
            
            return default_config
        
        config_dict = config.to_dict()
        self._processing_cache[cache_key] = (config_dict, time.time())
        config.last_used_at = datetime.utcnow()
        self.db_session.commit()
        
        # Cache in Redis if enabled
        if self.enable_redis_cache:
            try:
                field_cache = await self._get_field_cache()
                await field_cache.cache_field_config(client_id, collection_name, config_dict)
            except Exception as e:
                self.log_warning(f"Failed to cache config in Redis: {e}")
        
        return config_dict

    async def save_field_config(self, client_id: str, collection_name: str, 
                               field_config: Dict[str, Any]) -> None:
        """Save field configuration with Redis cache invalidation."""
        config = self.db_session.query(FieldConfig).filter_by(
            client_id=client_id, collection_name=collection_name
        ).first()
        
        if config:
            config.update_from_dict(field_config)
        else:
            config = FieldConfig.from_dict({
                **field_config, 
                'client_id': client_id, 
                'collection_name': collection_name
            })
            self.db_session.add(config)
        
        self.db_session.commit()
        
        # Invalidate local cache
        cache_key = f"{client_id}:{collection_name}"
        self._processing_cache.pop(cache_key, None)
        
        # Invalidate Redis cache and cache new config
        if self.enable_redis_cache:
            try:
                field_cache = await self._get_field_cache()
                await field_cache.invalidate_client_cache(client_id, collection_name)
                await field_cache.cache_field_config(client_id, collection_name, field_config)
            except Exception as e:
                self.log_warning(f"Failed to invalidate/update Redis cache: {e}")
    
    def extract_fields(self, content: Dict[str, Any], field_config: Dict[str, Any], 
                      language: str = None) -> Dict[str, Any]:
        """Extract fields with Redis caching for extraction results."""
        start_time = time.time()
        result = {}
        
        # Try Redis cache for extraction results if enabled
        cached_result = None
        if self.enable_redis_cache:
            try:
                field_cache = self._field_cache  # Use sync method since this is not async
                if field_cache:
                    # Note: This would need to be async, but extract_fields is sync
                    # We'll implement a sync wrapper or make this method async in future
                    pass
            except Exception as e:
                self.log_warning(f"Redis extraction cache error: {e}")
        
        try:
            field_paths = field_config["field_paths"]
            field_types = field_config.get("field_types", {})
            rtl_mapping = field_config.get("rtl_field_mapping", {})
            batch_processing = field_config.get("batch_processing", False)
            
            # Use RTL-specific mapping if applicable
            if language and is_rtl_language(language) and language in rtl_mapping:
                field_paths = rtl_mapping[language].get("field_paths", field_paths)
            
            # Handle batch processing
            if batch_processing:
                result = self._extract_fields_batch(content, field_paths, field_types, language)
            else:
                for path in field_paths:
                    value = self._get_nested_value(content, path)
                    if value is not None:
                        field_type = field_types.get(path, self._detect_field_type(value))
                        result[path] = {
                            "value": value,
                            "type": field_type,
                            "metadata": self._extract_metadata(value, field_type)
                        }
            
            # Log processing if enabled
            if self.enable_logging:
                self._log_processing(
                    client_id=field_config.get('client_id', 'unknown'),
                    collection_name=field_config.get('collection_name', 'unknown'),
                    operation_type='extract',
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    fields_processed=list(result.keys()),
                    success=True
                )
            
            return result
            
        except Exception as e:
            if self.enable_logging:
                self._log_processing(
                    client_id=field_config.get('client_id', 'unknown'),
                    collection_name=field_config.get('collection_name', 'unknown'),
                    operation_type='extract',
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    success=False,
                    error_message=str(e)
                )
            raise

    def _extract_fields_batch(self, content: Dict[str, Any], field_paths: List[str], 
                             field_types: Dict[str, str], language: str = None) -> Dict[str, Any]:
        """Extract fields in batch for efficient processing."""
        result = {}
        batch_text = []
        batch_mapping = {}
        
        for path in field_paths:
            value = self._get_nested_value(content, path)
            if value is not None:
                field_type = field_types.get(path, self._detect_field_type(value))
                
                if field_type in [FieldType.TEXT.value, FieldType.STRING.value, FieldType.TEXTAREA.value]:
                    batch_index = len(batch_text)
                    batch_text.append(value)
                    batch_mapping[path] = {"index": batch_index, "type": field_type}
                else:
                    result[path] = {
                        "value": value,
                        "type": field_type,
                        "metadata": self._extract_metadata(value, field_type)
                    }
        
        if batch_text:
            result["__batch__"] = {"text": batch_text, "mapping": batch_mapping}
        
        return result
    
    def _detect_field_type(self, value: Any) -> str:
        """Auto-detect field type based on content."""
        if isinstance(value, str):
            if self.is_html(value):
                return FieldType.WYSIWYG.value
            elif "\n" in value:
                return FieldType.TEXTAREA.value
            else:
                return FieldType.TEXT.value
        elif isinstance(value, dict):
            return FieldType.JSON.value
        else:
            return FieldType.STRING.value
    
    def _extract_metadata(self, value: Any, field_type: str) -> Dict[str, Any]:
        """Extract metadata to preserve during translation."""
        metadata = {}
        if field_type == FieldType.WYSIWYG.value and isinstance(value, str):
            metadata["html_structure"] = self._extract_html_structure(value)
        return metadata
    
    def _extract_html_structure(self, html: str) -> Dict[str, Any]:
        """Extract HTML structure for preservation."""
        soup = BeautifulSoup(html, 'html.parser')
        return {
            "tags": [tag.name for tag in soup.find_all()],
            "classes": [cls for tag in soup.find_all() for cls in tag.get("class", [])],
            "attributes": {tag.name: [attr for attr in tag.attrs if attr != "class"] 
                          for tag in soup.find_all() if tag.attrs}
        }
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation and array indices."""
        if not data or not path:
            return None
        
        parts = re.findall(r'([^\[\]\.]+)|\[(\d+)\]', path)
        current = data
        
        for part in parts:
            key, index = part
            if key and isinstance(current, dict):
                if key not in current:
                    return None
                current = current[key]
            elif index and isinstance(current, list):
                idx = int(index)
                if idx >= len(current):
                    return None
                current = current[idx]
            else:
                return None
        
        return current

    def is_html(self, text: str) -> bool:
        """Check if content is HTML."""
        return bool(re.search(r'<[^>]+>', text))
    
    def extract_text_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract text nodes from HTML for translation."""
        soup = BeautifulSoup(html, 'html.parser')
        text_nodes = []
        
        # Find all text nodes that are not just whitespace
        for element in soup.find_all(text=True):
            text_content = element.strip()
            if text_content and element.parent:
                # Store original element reference for easier reassembly
                text_nodes.append({
                    'text': text_content,
                    'element': element,  # Store reference to actual element
                    'parent_tag': element.parent.name,
                    'parent_attrs': element.parent.attrs if element.parent else {}
                })
        
        return text_nodes
    
    def _get_element_path(self, element) -> str:
        """Generate a path to the element for reassembly."""
        path = []
        current = element
        
        # Build path from current element to root
        while current and current.name and current.name != '[document]':
            siblings = current.parent.find_all(current.name, recursive=False) if current.parent else []
            if len(siblings) > 1:
                index = siblings.index(current)
                path.append(f"{current.name}:nth-of-type({index + 1})")
            else:
                path.append(current.name)
            current = current.parent
        
        # Return a valid CSS selector path
        if path:
            return " > ".join(reversed(path))
        return "body"
    
    def reassemble_html(self, original_html: str, translated_nodes: List[Dict[str, Any]]) -> str:
        """Reassemble HTML with translated text nodes."""
        soup = BeautifulSoup(original_html, 'html.parser')
        
        # Create a mapping of original text to translated text
        text_mapping = {}
        for node in translated_nodes:
            if 'translated_text' in node and 'text' in node:
                text_mapping[node['text']] = node['translated_text']
        
        # Replace text content in soup
        for element in soup.find_all(text=True):
            text_content = element.strip()
            if text_content and text_content in text_mapping:
                # Replace the text content while preserving HTML structure
                element.replace_with(text_mapping[text_content])
                
        return str(soup)
    
    def sanitize_content(self, content: Dict[str, Any], field_config: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize content before processing."""
        if not field_config.get("content_sanitization", True):
            return content
        
        sanitized = {}
        for path, field_data in content.items():
            if path == "__batch__":
                batch_text = field_data.get("text", [])
                sanitized_batch = []
                for text in batch_text:
                    if isinstance(text, str) and self.is_html(text):
                        soup = BeautifulSoup(text, 'html.parser')
                        for script in soup(["script", "style"]):
                            script.decompose()
                        sanitized_batch.append(str(soup))
                    else:
                        sanitized_batch.append(text)
                sanitized[path] = {
                    "text": sanitized_batch,
                    "mapping": field_data.get("mapping", {})
                }
            else:
                value = field_data.get("value")
                field_type = field_data.get("type")
                if field_type == FieldType.WYSIWYG.value and isinstance(value, str):
                    soup = BeautifulSoup(value, 'html.parser')
                    for script in soup(["script", "style"]):
                        script.decompose()
                    sanitized[path] = {
                        "value": str(soup),
                        "type": field_type,
                        "metadata": field_data.get("metadata", {})
                    }
                else:
                    sanitized[path] = field_data
        
        return sanitized

    def _log_processing(self, client_id: str, collection_name: str, operation_type: str,
                       processing_time_ms: int = None, fields_processed: List[str] = None,
                       success: bool = True, error_message: str = None) -> None:
        """Log processing operation for monitoring and debugging."""
        if not self.enable_logging:
            return
        
        try:
            log_entry = FieldProcessingLog(
                client_id=client_id,
                collection_name=collection_name,
                operation_type=operation_type,
                processing_time_ms=processing_time_ms,
                success=success,
                error_message=error_message
            )
            self.db_session.add(log_entry)
            self.db_session.commit()
        except Exception as e:
            # Don't fail the main operation if logging fails
            print(f"Warning: Failed to log processing operation: {e}")
    
    def log_warning(self, message: str) -> None:
        """Log warning message."""
        print(f"FieldMapper Warning: {message}")
    
    async def invalidate_cache(self, client_id: str, collection_name: str = None) -> Dict[str, int]:
        """Invalidate caches for client/collection."""
        result = {'local_cache': 0, 'redis_cache': 0}
        
        # Invalidate local cache
        if collection_name:
            cache_key = f"{client_id}:{collection_name}"
            if self._processing_cache.pop(cache_key, None):
                result['local_cache'] = 1
        else:
            # Invalidate all client caches
            keys_to_remove = [k for k in self._processing_cache.keys() if k.startswith(f"{client_id}:")]
            for key in keys_to_remove:
                self._processing_cache.pop(key, None)
            result['local_cache'] = len(keys_to_remove)
        
        # Invalidate Redis cache
        if self.enable_redis_cache:
            try:
                field_cache = await self._get_field_cache()
                result['redis_cache'] = await field_cache.invalidate_client_cache(client_id, collection_name)
            except Exception as e:
                self.log_warning(f"Failed to invalidate Redis cache: {e}")
        
        return result
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive caching statistics."""
        stats = {
            'local_cache': {
                'entries': len(self._processing_cache),
                'keys': list(self._processing_cache.keys())
            },
            'redis_cache': None,
            'redis_enabled': self.enable_redis_cache
        }
        
        if self.enable_redis_cache:
            try:
                field_cache = await self._get_field_cache()
                stats['redis_cache'] = await field_cache.get_cache_stats()
            except Exception as e:
                stats['redis_cache'] = {'error': str(e)}
        
        return stats
    
    async def warm_cache_from_database(self, client_id: str = None) -> Dict[str, int]:
        """Warm Redis cache with configurations from database."""
        if not self.enable_redis_cache:
            return {'error': 'Redis cache not enabled'}
        
        try:
            query = self.db_session.query(FieldConfig)
            if client_id:
                query = query.filter_by(client_id=client_id)
            
            configs = query.all()
            config_list = []
            
            for config in configs:
                config_data = {
                    'client_id': config.client_id,
                    'collection_name': config.collection_name,
                    'field_config': config.to_dict()
                }
                config_list.append(config_data)
            
            field_cache = await self._get_field_cache()
            return await field_cache.warm_cache(config_list)
            
        except Exception as e:
            self.log_warning(f"Failed to warm cache from database: {e}")
            return {'error': str(e)}
    
    def handle_directus_translations(self, content: Dict[str, Any], field_config: Dict[str, Any], 
                                    language: str) -> Dict[str, Any]:
        """Handle Directus translation patterns."""
        pattern = field_config.get("directus_translation_pattern", 
                                  DirectusTranslationPattern.COLLECTION_TRANSLATIONS.value)
        
        if pattern == DirectusTranslationPattern.COLLECTION_TRANSLATIONS.value:
            return self._handle_collection_translations(content, field_config, language)
        elif pattern == DirectusTranslationPattern.LANGUAGE_COLLECTIONS.value:
            return self._handle_language_collections(content, field_config, language)
        else:
            return self.extract_fields(content, field_config, language)
    
    def _handle_collection_translations(self, content: Dict[str, Any], field_config: Dict[str, Any], 
                                      language: str) -> Dict[str, Any]:
        """Handle standard Directus translation pattern with collection_translations."""
        result = {}
        primary_collection = field_config.get("primary_collection")
        
        if not primary_collection or not content.get("id"):
            return result
        
        result = {
            "id": None,
            primary_collection + "_id": content.get("id"),
            "languages_code": language,
        }
        
        extracted = self.extract_fields(content, field_config, language)
        for path, field_data in extracted.items():
            if "__batch__" not in path:
                field_name = path.split(".")[-1]
                result[field_name] = field_data.get("value")
        
        return result
    
    def _handle_language_collections(self, content: Dict[str, Any], field_config: Dict[str, Any], 
                                   language: str) -> Dict[str, Any]:
        """Handle language-specific collections pattern."""
        result = {"id": content.get("id")}
        
        extracted = self.extract_fields(content, field_config, language)
        for path, field_data in extracted.items():
            if "__batch__" not in path:
                field_name = path.split(".")[-1]
                result[field_name] = field_data.get("value")
        
        return result


# Export the main class
__all__ = ['FieldMapper']
