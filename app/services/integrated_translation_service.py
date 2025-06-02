"""
Integrated Translation Service - Combines field mapping with flexible AI translation providers.
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from .field_mapper import FieldMapper
from .flexible_translation_service import FlexibleTranslationService
from .content_processor import ContentProcessor
from .translation_provider import TranslationResult, TranslationError, LanguageDirection
from ..models.field_config import FieldProcessingLog
from ..models.field_types import FieldType, DirectusTranslationPattern

logger = logging.getLogger(__name__)


class IntegratedTranslationService:
    """
    Integrated service combining field mapping with flexible AI translation providers.
    Uses client-specified provider/model with field mapping for structured content translation.
    """

    def __init__(self, db_session: Session):
        """Initialize the integrated translation service."""
        self.db_session = db_session
        self.field_mapper = FieldMapper(db_session)
        self.translation_service = FlexibleTranslationService()
        self.content_processor = ContentProcessor()
        logger.info("Initialized IntegratedTranslationService with flexible provider selection")

    async def translate_structured_content(
        self,
        content: Dict[str, Any],
        client_id: str,
        collection_name: str,
        source_lang: str,
        target_lang: str,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate structured content using field mapping and specified AI provider.

        Args:
            content: Input content to translate
            client_id: Client identifier
            collection_name: Collection name for field mapping
            source_lang: Source language code
            target_lang: Target language code
            provider: AI provider to use ('openai', 'anthropic', 'mistral', 'deepseek')
            api_key: API key for the specified provider
            model: Specific model to use (optional, uses provider default)
            context: Optional context for translation

        Returns:
            Dict containing translated content and metadata
        """
        start_time = time.time()
        
        try:
            # 1. Get field configuration            logger.info(f"Starting structured content translation: {client_id}/{collection_name}, {source_lang}->{target_lang}, provider: {provider}")
            
            field_config = await self.field_mapper.get_field_config(client_id, collection_name)
            if not field_config.get("field_paths"):
                logger.warning(f"No field configuration found for {client_id}/{collection_name}")
                return {
                    "translated_content": content,
                    "metadata": {
                        "warning": "No field mapping configuration - content returned unchanged",
                        "processing_time_ms": int((time.time() - start_time) * 1000)
                    }
                }

            # 2. Extract translatable fields using field mapping
            extracted_fields = self.field_mapper.extract_fields(content, field_config, target_lang)
            
            # 3. Sanitize content if enabled
            if field_config.get("content_sanitization", True):
                extracted_fields = self.field_mapper.sanitize_content(extracted_fields, field_config)

            # 4. Translate extracted fields
            translation_results = {}
            
            if field_config.get("batch_processing", False) and "__batch__" in extracted_fields:
                # Handle batch translation
                batch_translation_results = await self._translate_batch_fields(
                    extracted_fields["__batch__"], source_lang, target_lang, 
                    provider, api_key, model, context
                )
                # Convert TranslationResult objects to dicts
                for field_path, translation_result in batch_translation_results.items():
                    translation_results[field_path] = {
                        "translated_text": translation_result.translated_text,
                        "provider_used": translation_result.provider_used,
                        "source_lang": translation_result.source_lang,
                        "target_lang": translation_result.target_lang,
                        "quality_score": translation_result.quality_score,
                        "metadata": translation_result.metadata
                    }
                # Remove batch metadata
                extracted_fields = {k: v for k, v in extracted_fields.items() if k != "__batch__"}

            # Handle individual fields
            for field_path, field_data in extracted_fields.items():
                if field_path not in translation_results:
                    translation_result = await self._translate_single_field(
                        field_data, field_path, source_lang, target_lang, 
                        provider, api_key, model, context
                    )
                    # Convert TranslationResult to dict for JSON serialization
                    translation_results[field_path] = {
                        "translated_text": translation_result.translated_text,
                        "provider_used": translation_result.provider_used,
                        "source_lang": translation_result.source_lang,
                        "target_lang": translation_result.target_lang,
                        "quality_score": translation_result.quality_score,
                        "metadata": translation_result.metadata
                    }

            # 5. Reconstruct translated content
            translated_content = await self._reconstruct_content(
                content, translation_results, field_config, target_lang
            )

            # 6. Log processing operation
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self._log_processing_operation(
                client_id, collection_name, "translate", "success", 
                len(translation_results), processing_time_ms
            )

            return {
                "translated_content": translated_content,
                "field_translations": translation_results,
                "metadata": {
                    "client_id": client_id,
                    "collection_name": collection_name,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "provider_used": provider,
                    "model_used": model,
                    "fields_translated": len(translation_results),
                    "batch_processing": field_config.get("batch_processing", False),
                    "processing_time_ms": processing_time_ms,
                    "language_direction": self.translation_service.get_language_direction(target_lang).value
                }
            }

        except Exception as e:
            # Log error
            processing_time_ms = int((time.time() - start_time) * 1000)
            await self._log_processing_operation(
                client_id, collection_name, "translate", "error", 
                0, processing_time_ms, str(e)
            )
            logger.error(f"Translation failed for {client_id}/{collection_name}: {str(e)}")
            raise TranslationError(f"Structured content translation failed: {str(e)}")

    async def _translate_batch_fields(
        self,
        batch_data: Dict[str, Any],
        source_lang: str,
        target_lang: str,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, TranslationResult]:
        """Translate fields in batch for efficiency."""
        batch_texts = batch_data.get("text", [])
        batch_mapping = batch_data.get("mapping", {})
        
        if not batch_texts:
            return {}

        # Perform batch translation
        batch_results = await self.translation_service.batch_translate(
            batch_texts, source_lang, target_lang, provider, api_key, model, context
        )

        # Map results back to field paths
        translation_results = {}
        for field_path, mapping_info in batch_mapping.items():
            batch_index = mapping_info.get("index")
            if batch_index is not None and batch_index < len(batch_results):
                translation_results[field_path] = batch_results[batch_index]

        return translation_results

    async def _translate_single_field(
        self,
        field_data: Dict[str, Any],
        field_path: str,
        source_lang: str,
        target_lang: str,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        context: Optional[str] = None
    ) -> TranslationResult:
        """Translate a single field."""
        field_value = field_data.get("value", "")
        field_type = field_data.get("type", FieldType.TEXT.value)
        field_metadata = field_data.get("metadata", {})

        if not field_value or not isinstance(field_value, str):
            raise TranslationError(f"Invalid field value for translation: {field_path}")

        # Handle HTML content specially
        if field_type == FieldType.WYSIWYG.value:
            return await self._translate_html_content(
                field_value, field_metadata, source_lang, target_lang,
                provider, api_key, model, context
            )
        else:
            # Standard text translation
            return await self.translation_service.translate(
                field_value, source_lang, target_lang, provider, api_key, model, context
            )

    async def _translate_html_content(
        self,
        html_content: str,
        html_metadata: Dict[str, Any],
        source_lang: str,
        target_lang: str,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        context: Optional[str] = None
    ) -> TranslationResult:
        """Translate HTML content while preserving structure."""
        # Check if target language is RTL
        rtl_languages = ['ar', 'he', 'fa', 'ur']
        is_rtl = target_lang in rtl_languages
        
        # For RTL languages, use a different approach to maintain proper text flow
        if is_rtl:
            return await self._translate_html_content_rtl(
                html_content, html_metadata, source_lang, target_lang,
                provider, api_key, model, context
            )
        
        # For LTR languages, use the original approach
        return await self._translate_html_content_ltr(
            html_content, html_metadata, source_lang, target_lang,
            provider, api_key, model, context
        )
    
    async def _translate_html_content_rtl(
        self,
        html_content: str,
        html_metadata: Dict[str, Any],
        source_lang: str,
        target_lang: str,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        context: Optional[str] = None
    ) -> TranslationResult:
        """Translate HTML content for RTL languages with proper text flow."""
        # Extract text nodes from HTML (same as LTR but with RTL-specific context)
        text_nodes = self.field_mapper.extract_text_from_html(html_content)
        
        if not text_nodes:
            return TranslationResult(
                translated_text=html_content,
                provider_used=provider,
                source_lang=source_lang,
                target_lang=target_lang,
                quality_score=1.0,
                metadata={"html_preserved": True, "no_text_found": True}
            )

        # Translate individual text nodes with RTL-specific constraints
        translated_nodes = []
        for node in text_nodes:
            try:
                # RTL-specific context for better Arabic sentence structure
                rtl_context = f"HTML fragment translation to {target_lang}. Translate ONLY this exact text segment: '{node['text']}'. Use natural {target_lang} word order and sentence flow that reads naturally from right to left. Do not add any additional words, explanations, or content."
                
                result = await self.translation_service.translate(
                    node["text"], source_lang, target_lang, provider, api_key, model, rtl_context
                )
                
                translated_nodes.append({
                    **node,  # Copy all original node data
                    "translated_text": result.translated_text
                })
                
            except Exception as e:
                logger.warning(f"Failed to translate HTML text node '{node['text']}': {str(e)}")
                # Keep original text if translation fails
                translated_nodes.append({
                    **node,  # Copy all original node data
                    "translated_text": node["text"]
                })

        # Reassemble HTML with translated text nodes
        translated_html = self.field_mapper.reassemble_html(html_content, translated_nodes)
        
        return TranslationResult(
            translated_text=translated_html,
            provider_used=provider,
            source_lang=source_lang,
            target_lang=target_lang,
            quality_score=0.9,  # Default quality score
            metadata={
                "html_preserved": True,
                "rtl_optimized": True,
                "original_structure": html_metadata.get("html_structure", {}),
                "translation_approach": "node_by_node_rtl",
                "nodes_translated": len(translated_nodes)
            }
        )
    
    async def _translate_html_content_ltr(
        self,
        html_content: str,
        html_metadata: Dict[str, Any],
        source_lang: str,
        target_lang: str,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        context: Optional[str] = None
    ) -> TranslationResult:
        """Translate HTML content for LTR languages (original approach)."""
        # Extract text nodes from HTML
        text_nodes = self.field_mapper.extract_text_from_html(html_content)
        
        if not text_nodes:
            return TranslationResult(
                translated_text=html_content,
                provider_used=provider,
                source_lang=source_lang,
                target_lang=target_lang,
                quality_score=1.0,
                metadata={"html_preserved": True, "no_text_found": True}
            )

        # Translate individual text nodes with HTML-specific constraints
        translated_nodes = []
        for node in text_nodes:
            try:
                html_context = f"HTML fragment translation. Translate ONLY this exact text segment: '{node['text']}'. Do not add any additional words, explanations, or content. Preserve the exact meaning and length."
                
                result = await self.translation_service.translate(
                    node["text"], source_lang, target_lang, provider, api_key, model, html_context
                )
                translated_nodes.append({
                    **node,
                    "translated_text": result.translated_text
                })
            except TranslationError:
                translated_nodes.append({
                    **node,
                    "translated_text": node["text"]
                })

        # Reassemble HTML with translated text
        translated_html = self.field_mapper.reassemble_html(html_content, translated_nodes)

        return TranslationResult(
            translated_text=translated_html,
            provider_used=provider,
            source_lang=source_lang,
            target_lang=target_lang,
            quality_score=1.0,
            metadata={
                "html_preserved": True,
                "text_nodes_translated": len(translated_nodes),
                "html_structure": html_metadata.get("html_structure", {}),
                "translation_approach": "fragment_based_ltr"
            }
        )

    async def _reconstruct_content(
        self,
        original_content: Dict[str, Any],
        translation_results: Dict[str, Dict[str, Any]],
        field_config: Dict[str, Any],
        target_lang: str
    ) -> Dict[str, Any]:
        """Reconstruct content with translated fields."""
        translated_content = original_content.copy()

        # Handle Directus translation patterns
        translation_pattern = field_config.get("directus_translation_pattern")
        if translation_pattern:
            return self._apply_directus_pattern(
                translated_content, translation_results, field_config, target_lang
            )

        # Standard field replacement
        for field_path, translation_result in translation_results.items():
            translated_text = translation_result.get("translated_text", "")
            if field_path in translated_content:
                translated_content[field_path] = translated_text
            else:
                # Handle nested field paths
                self._set_nested_value(translated_content, field_path, translated_text)

        # Add translation metadata
        translated_content["_translation_metadata"] = {
            "translated_at": datetime.utcnow().isoformat(),
            "target_language": target_lang,
            "fields_translated": list(translation_results.keys()),
            "provider_stats": self._get_provider_stats(translation_results)
        }

        return translated_content

    def _apply_directus_pattern(
        self,
        content: Dict[str, Any],
        translation_results: Dict[str, Dict[str, Any]],
        field_config: Dict[str, Any],
        target_lang: str
    ) -> Dict[str, Any]:
        """Apply Directus-specific translation patterns."""
        pattern = field_config.get("directus_translation_pattern")
        
        if pattern == DirectusTranslationPattern.COLLECTION_TRANSLATIONS.value:
            return self._apply_collection_translations_pattern(
                content, translation_results, field_config, target_lang
            )
        elif pattern == DirectusTranslationPattern.LANGUAGE_COLLECTIONS.value:
            return self._apply_language_collections_pattern(
                content, translation_results, field_config, target_lang
            )
        else:
            # Custom pattern - use standard reconstruction
            return self._reconstruct_content(content, translation_results, {}, target_lang)

    def _apply_collection_translations_pattern(
        self,
        content: Dict[str, Any],
        translation_results: Dict[str, Dict[str, Any]],
        field_config: Dict[str, Any],
        target_lang: str
    ) -> Dict[str, Any]:
        """Apply collection_translations pattern."""
        primary_collection = field_config.get("primary_collection")
        
        result = {
            "id": None,  # Will be set by Directus
            f"{primary_collection}_id": content.get("id"),
            "languages_code": target_lang,
        }

        # Add translated fields
        for field_path, translation_result in translation_results.items():
            field_name = field_path.split(".")[-1]  # Get field name without path
            result[field_name] = translation_result.get("translated_text", "")

        return result

    def _apply_language_collections_pattern(
        self,
        content: Dict[str, Any],
        translation_results: Dict[str, Dict[str, Any]],
        field_config: Dict[str, Any],
        target_lang: str
    ) -> Dict[str, Any]:
        """Apply language_collections pattern."""
        result = {
            "id": content.get("id"),  # Same ID as original
        }

        # Add translated fields
        for field_path, translation_result in translation_results.items():
            field_name = field_path.split(".")[-1]  # Get field name without path
            result[field_name] = translation_result.get("translated_text", "")

        return result

    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set value in nested dictionary using dot notation."""
        keys = path.split(".")
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value

    def _get_provider_stats(self, translation_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Get provider statistics from translation results."""
        stats = {}
        quality_scores = []
        
        for result in translation_results.values():
            provider = result.get("provider_used", "unknown")
            quality_score = result.get("quality_score", 0.0)
            
            if provider not in stats:
                stats[provider] = {"count": 0, "quality_scores": []}
            
            stats[provider]["count"] += 1
            stats[provider]["quality_scores"].append(quality_score)
            quality_scores.append(quality_score)

        # Calculate averages
        for provider in stats:
            scores = stats[provider]["quality_scores"]
            stats[provider]["avg_quality"] = sum(scores) / len(scores) if scores else 0.0

        return {
            "providers": stats,
            "overall_avg_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        }

    async def _log_processing_operation(
        self,
        client_id: str,
        collection_name: str,
        operation: str,
        status: str,
        fields_processed: int,
        processing_time_ms: int,
        error_message: Optional[str] = None
    ) -> None:
        """Log processing operation to database."""
        try:
            log_entry = FieldProcessingLog(
                client_id=client_id,
                collection_name=collection_name,
                operation_type=operation,
                success=(status == "success"),
                processing_time_ms=processing_time_ms,
                error_message=error_message
            )
            self.db_session.add(log_entry)
            self.db_session.commit()
        except Exception as e:
            logger.error(f"Failed to log processing operation: {str(e)}")

    async def validate_translation_request(
        self,
        client_id: str,
        collection_name: str,
        provider: str,
        api_key: str,
        source_lang: str,
        target_lang: str
    ) -> Dict[str, Any]:
        """Validate a translation request."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # Check field configuration exists
        field_config = await self.field_mapper.get_field_config(client_id, collection_name)
        if not field_config.get("field_paths"):
            validation_result["warnings"].append(
                f"No field mapping configuration found for {client_id}/{collection_name}"
            )

        # Validate provider
        available_providers = self.translation_service.get_available_providers()
        if provider not in available_providers:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Unsupported provider: {provider}. Available: {available_providers}"
            )

        # Validate language support
        supported_languages = self.translation_service.get_supported_languages(provider)
        if source_lang not in supported_languages:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Unsupported source language: {source_lang}")
        
        if target_lang not in supported_languages:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Unsupported target language: {target_lang}")

        # Validate API key
        try:
            key_valid = await self.translation_service.validate_api_key(provider, api_key)
            if not key_valid:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Invalid API key for provider: {provider}")
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"API key validation failed: {str(e)}")

        return validation_result

    async def get_translation_preview(
        self,
        content: Dict[str, Any],
        client_id: str,
        collection_name: str,
        target_lang: str
    ) -> Dict[str, Any]:
        """Get a preview of what would be translated without actually translating."""
        field_config = await self.field_mapper.get_field_config(client_id, collection_name)
        
        if not field_config.get("field_paths"):
            return {
                "extractable_fields": {},
                "warning": "No field mapping configuration found"
            }

        # Extract fields that would be translated
        extracted_fields = self.field_mapper.extract_fields(content, field_config, target_lang)
        
        # Build preview
        preview = {}
        for field_path, field_data in extracted_fields.items():
            if field_path == "__batch__":
                # Handle batch preview
                batch_data = field_data
                batch_mapping = batch_data.get("mapping", {})
                for path, mapping_info in batch_mapping.items():
                    batch_index = mapping_info.get("index")
                    if batch_index is not None and batch_index < len(batch_data.get("text", [])):
                        preview[path] = {
                            "content": batch_data["text"][batch_index],
                            "type": mapping_info.get("type"),
                            "batch_processing": True
                        }
            else:
                preview[field_path] = {
                    "content": field_data.get("value"),
                    "type": field_data.get("type"),
                    "metadata": field_data.get("metadata", {}),
                    "batch_processing": False
                }

        return {
            "extractable_fields": preview,
            "field_config": {
                "total_fields": len(field_config.get("field_paths", [])),
                "batch_processing": field_config.get("batch_processing", False),
                "directus_pattern": field_config.get("directus_translation_pattern"),
                "rtl_support": target_lang in field_config.get("rtl_field_mapping", {})
            }
        }

