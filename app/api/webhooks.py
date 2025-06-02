"""
Webhook API endpoints for Directus CMS integration - Fixed validation issues.
"""
import hashlib
import hmac
import json
import time
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Request, Header, Depends
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.integrated_translation_service import IntegratedTranslationService
from ..services.field_mapper import FieldMapper
from ..config import settings
from ..services import TranslationError

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class DirectusWebhookRequest(BaseModel):
    """Request model for Directus webhook payload."""
    event: str = Field(..., description="Directus event type (items.create, items.update, etc.)")
    collection: str = Field(..., description="Collection name that triggered the event")
    key: Any = Field(..., description="Item ID or composite key")
    data: Dict[str, Any] = Field(..., description="Item data from Directus")
    
    # LocPlat-specific fields (added by Directus Flow)
    client_id: str = Field(..., description="Client identifier", min_length=1, max_length=100)
    target_language: str = Field(..., description="Target language code (e.g., 'ar', 'bs')")
    provider: str = Field(..., description="AI provider ('openai', 'anthropic', 'mistral', 'deepseek')")
    api_key: str = Field(..., description="API key for the specified provider", min_length=10, max_length=200)
    model: Optional[str] = Field(None, description="Model name (optional)", max_length=100)
    context: Optional[str] = Field(None, description="Optional context for translation", max_length=500)
    
    # Optional configuration overrides
    source_language: Optional[str] = Field("en", description="Source language code (default: 'en')")
    translation_pattern: Optional[str] = Field(None, description="Override translation pattern")
    batch_processing: Optional[bool] = Field(None, description="Override batch processing setting")

    @validator('target_language', 'source_language')
    def validate_language_codes(cls, v):
        if v and len(v.strip()) != 2:
            raise ValueError("Language codes must be 2 characters long")
        return v.lower().strip() if v else v

    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = ["openai", "anthropic", "mistral", "deepseek"]
        if not v or v.lower().strip() not in valid_providers:
            raise ValueError(f"Provider must be one of: {valid_providers}")
        return v.lower().strip()

    @validator('event')
    def validate_event(cls, v):
        valid_events = [
            "items.create", "items.update", "items.delete",
            "flow.operation", "custom.translate"
        ]
        if not v or v not in valid_events:
            raise ValueError(f"Event must be one of: {valid_events}")
        return v

    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("API key must be at least 10 characters long")
        import re
        cleaned_key = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        if re.search(r'(?i)(system|user|assistant)\s*:', cleaned_key):
            raise ValueError("Invalid API key format")
        return cleaned_key.strip()

    @validator('client_id', 'collection')
    def validate_required_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @validator('data')
    def validate_data(cls, v):
        if not v or not isinstance(v, dict):
            raise ValueError("Data must be a valid JSON object")
        return v


class DirectusWebhookResponse(BaseModel):
    """Response model for Directus webhook."""
    success: bool
    operation: str  # "insert", "update", "skip"
    collection: str
    translated_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebhookValidationRequest(BaseModel):
    """Request model for webhook validation - FIXED VERSION."""
    client_id: str = Field(..., description="Client identifier", min_length=1, max_length=100)
    collection: str = Field(..., description="Collection name", min_length=1, max_length=100)
    provider: str = Field(..., description="AI provider")
    api_key: str = Field(..., description="API key", min_length=10)
    target_language: str = Field(..., description="Target language code")
    
    @validator('target_language')
    def validate_target_language(cls, v):
        if not v or len(v.strip()) != 2:
            raise ValueError("Language code must be 2 characters long")
        return v.lower().strip()

    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = ["openai", "anthropic", "mistral", "deepseek"]
        if not v or v.lower().strip() not in valid_providers:
            raise ValueError(f"Provider must be one of: {valid_providers}")
        return v.lower().strip()

    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("API key must be at least 10 characters long")
        # Remove any control characters and validate format
        import re
        cleaned_key = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        if re.search(r'(?i)(system|user|assistant)\s*:', cleaned_key):
            raise ValueError("Invalid API key format")
        return cleaned_key.strip()

    @validator('client_id', 'collection')
    def validate_required_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class WebhookTestRequest(BaseModel):
    """Request model for webhook testing."""
    sample_data: Dict[str, Any] = Field(..., description="Sample content data")
    client_id: str = Field(..., description="Client identifier", min_length=1, max_length=100)
    collection: str = Field(..., description="Collection name", min_length=1, max_length=100)
    target_language: str = Field(..., description="Target language code")
    provider: str = Field(..., description="AI provider")
    api_key: str = Field(..., description="API key", min_length=10)
    dry_run: bool = Field(True, description="Whether to perform actual translation")

    @validator('target_language')
    def validate_target_language(cls, v):
        if not v or len(v.strip()) != 2:
            raise ValueError("Language code must be 2 characters long")
        return v.lower().strip()

    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = ["openai", "anthropic", "mistral", "deepseek"]
        if not v or v.lower().strip() not in valid_providers:
            raise ValueError(f"Provider must be one of: {valid_providers}")
        return v.lower().strip()

    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("API key must be at least 10 characters long")
        import re
        cleaned_key = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        if re.search(r'(?i)(system|user|assistant)\s*:', cleaned_key):
            raise ValueError("Invalid API key format")
        return cleaned_key.strip()

    @validator('client_id', 'collection')
    def validate_required_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @validator('sample_data')
    def validate_sample_data(cls, v):
        if not v or not isinstance(v, dict):
            raise ValueError("Sample data must be a valid JSON object")
        return v


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """
    Verify webhook signature for security.
    Supports both SHA-256 and SHA-1 signatures from Directus.
    """
    if not signature or not secret:
        return False
    
    try:
        # Handle different signature formats
        if signature.startswith('sha256='):
            expected_signature = 'sha256=' + hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
        elif signature.startswith('sha1='):
            expected_signature = 'sha1=' + hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha1
            ).hexdigest()
        else:
            # Assume SHA-256 without prefix
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False


@router.post("/directus/translate", response_model=DirectusWebhookResponse)
async def directus_translation_webhook(
    request: DirectusWebhookRequest,
    raw_request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_directus_signature: Optional[str] = Header(None, alias="X-Directus-Signature"),
    db: Session = Depends(get_db)
):
    """
    Main Directus webhook endpoint for automatic content translation.
    
    This endpoint receives webhook calls from Directus when content is created or updated.
    It processes the content through field mapping, translates it using AI, and returns
    the translated data in a format ready for Directus to store.
    
    **Webhook Security:**
    - Supports signature verification (X-Signature or X-Directus-Signature headers)
    - Validates webhook payload structure and required fields
    
    **Translation Process:**
    1. Validates webhook signature (if provided)
    2. Extracts translatable fields using field mapping configuration
    3. Translates content using specified AI provider
    4. Formats response for Directus translation collections
    5. Returns structured data ready for upsert operation
    
    **Directus Flow Setup Example:**
    ```yaml
    trigger: Event Hook (items.update on your collection)
    operation: Webhook (POST to this endpoint)
    next: Upsert into translation collection
    ```
    """
    start_time = time.time()
    
    try:
        # Get raw request body for signature verification
        raw_body = await raw_request.body()
        
        # Verify webhook signature if provided and secret is configured
        signature = x_signature or x_directus_signature
        if signature and settings.WEBHOOK_SECRET:
            if not verify_webhook_signature(raw_body, signature, settings.WEBHOOK_SECRET):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid webhook signature"
                )
        
        # Skip delete events
        if request.event == "items.delete":
            return DirectusWebhookResponse(
                success=True,
                operation="skip",
                collection=request.collection,
                metadata={
                    "reason": "Delete events are not processed for translation",
                    "event": request.event
                }
            )
        
        # Initialize integrated translation service
        integrated_service = IntegratedTranslationService(db)
        
        # Check if this is a translation collection to avoid infinite loops
        field_config = await integrated_service.field_mapper.get_field_config(
            request.client_id, 
            request.collection
        )
        
        if field_config.get("is_translation_collection", False):
            return DirectusWebhookResponse(
                success=True,
                operation="skip",
                collection=request.collection,
                metadata={
                    "reason": "Translation collection events are skipped to prevent loops",
                    "collection": request.collection
                }
            )
        
        # Perform structured translation
        translation_result = await integrated_service.translate_structured_content(
            content=request.data,
            client_id=request.client_id,
            collection_name=request.collection,
            source_lang=request.source_language or "en",
            target_lang=request.target_language,
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            context=request.context
        )
        
        # Determine operation based on translation pattern
        translation_pattern = field_config.get("directus_translation_pattern", "collection_translations")
        
        if translation_pattern == "collection_translations":
            # Standard Directus translation pattern
            target_collection = f"{request.collection}_translations"
            operation = "upsert"  # Directus should handle existing translations
        elif translation_pattern == "language_collections":
            # Language-specific collections (e.g., articles_ar, articles_bs)
            target_collection = f"{request.collection}_{request.target_language}"
            operation = "update"  # Update the record with same ID
        else:
            # Custom pattern
            target_collection = request.collection
            operation = "insert"
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        return DirectusWebhookResponse(
            success=True,
            operation=operation,
            collection=target_collection,
            translated_data=translation_result,
            metadata={
                "processing_time_ms": processing_time,
                "source_language": request.source_language or "en",
                "target_language": request.target_language,
                "provider_used": request.provider,
                "model_used": request.model or "default",
                "translation_pattern": translation_pattern,
                "fields_processed": len(translation_result.get("extracted_fields", {})),
                "event": request.event,
                "webhook_timestamp": int(time.time())
            }
        )

    except TranslationError as e:
        return DirectusWebhookResponse(
            success=False,
            operation="error",
            collection=request.collection,
            error=f"Translation error: {str(e)}",
            metadata={
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "error_type": "translation_error",
                "event": request.event
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return DirectusWebhookResponse(
            success=False,
            operation="error",
            collection=request.collection,
            error=f"Webhook processing error: {str(e)}",
            metadata={
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                "error_type": "processing_error",
                "event": request.event
            }
        )


@router.post("/directus/validate")
async def validate_webhook_configuration(
    request: WebhookValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Validate webhook configuration before setting up in Directus - FIXED VERSION.
    
    Checks:
    - Field mapping configuration exists for the collection
    - API key is valid for the specified provider
    - Provider supports the target language
    - Directus translation pattern is properly configured
    """
    try:
        integrated_service = IntegratedTranslationService(db)
        
        # Get field configuration
        field_config = await integrated_service.field_mapper.get_field_config(
            request.client_id, 
            request.collection
        )
        
        if not field_config.get("field_paths"):
            raise HTTPException(
                status_code=400,
                detail=f"No field mapping configuration found for {request.client_id}/{request.collection}"
            )
        
        # Validate API key
        from ..services.flexible_translation_service import FlexibleTranslationService
        translation_service = FlexibleTranslationService()
        
        is_valid_key = await translation_service.validate_api_key(
            request.provider, 
            request.api_key
        )
        
        if not is_valid_key:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid API key for provider '{request.provider}'"
            )
        
        # Check language support
        supported_languages = translation_service.get_supported_languages(request.provider)
        if request.target_language not in supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Language '{request.target_language}' not supported by {request.provider}"
            )
        
        return {
            "success": True,
            "message": "Webhook configuration is valid",
            "data": {
                "collection": request.collection,
                "field_paths_count": len(field_config.get("field_paths", [])),
                "translation_pattern": field_config.get("directus_translation_pattern", "collection_translations"),
                "batch_processing": field_config.get("batch_processing", False),
                "provider": request.provider,
                "target_language": request.target_language,
                "api_key_valid": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}"
        ) from e


@router.post("/directus/test")
async def test_webhook_processing(
    request: WebhookTestRequest,
    db: Session = Depends(get_db)
):
    """
    Test webhook processing with sample data - FIXED VERSION.
    
    This endpoint allows testing the webhook flow without setting up actual
    Directus webhooks. It processes sample data through the same pipeline
    and returns what would be sent back to Directus.
    """
    try:
        integrated_service = IntegratedTranslationService(db)
        
        if request.dry_run:
            # Preview mode - don't actually translate
            preview = await integrated_service.get_translation_preview(
                content=request.sample_data,
                client_id=request.client_id,
                collection_name=request.collection,
                target_lang=request.target_language
            )
            
            return {
                "success": True,
                "operation": "preview",
                "data": preview,
                "metadata": {
                    "dry_run": True,
                    "provider": request.provider,
                    "target_language": request.target_language
                }
            }
        else:
            # Actual translation test
            result = await integrated_service.translate_structured_content(
                content=request.sample_data,
                client_id=request.client_id,
                collection_name=request.collection,
                source_lang="en",  # Default for testing
                target_lang=request.target_language,
                provider=request.provider,
                api_key=request.api_key
            )
            
            return {
                "success": True,
                "operation": "translate",
                "data": result,
                "metadata": {
                    "dry_run": False,
                    "provider": request.provider,
                    "target_language": request.target_language
                }
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test error: {str(e)}"
        ) from e


@router.get("/directus/info")
async def get_webhook_info():
    """
    Get information about webhook endpoints and setup instructions.
    
    Returns documentation and examples for setting up Directus webhooks.
    """
    return {
        "webhook_url": "/api/v1/webhooks/directus/translate",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "X-Signature": "Optional: sha256=<signature> for security"
        },
        "security": {
            "signature_verification": "Supports SHA-256 and SHA-1 HMAC signatures",
            "headers": ["X-Signature", "X-Directus-Signature"]
        },
        "directus_flow_example": {
            "trigger": {
                "type": "Event Hook",
                "collections": ["your_collection"],
                "actions": ["create", "update"]
            },
            "operation": {
                "type": "Webhook",
                "method": "POST",
                "url": "{{$env.LOCPLAT_WEBHOOK_URL}}/api/v1/webhooks/directus/translate",
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": {
                    "event": "{{$trigger.event}}",
                    "collection": "{{$trigger.collection}}",
                    "key": "{{$trigger.key}}",
                    "data": "{{$trigger.payload}}",
                    "client_id": "{{$env.CLIENT_ID}}",
                    "target_language": "ar",
                    "provider": "openai",
                    "api_key": "{{$env.OPENAI_API_KEY}}"
                }
            },
            "next_operation": {
                "type": "Update Data",
                "collection": "{{$last.collection}}",
                "payload": "{{$last.translated_data}}",
                "operation": "{{$last.operation}}"
            }
        },
        "supported_events": [
            "items.create",
            "items.update", 
            "flow.operation",
            "custom.translate"
        ],
        "required_fields": [
            "event", "collection", "key", "data",
            "client_id", "target_language", "provider", "api_key"
        ],
        "optional_fields": [
            "model", "context", "source_language", "translation_pattern",
            "batch_processing", "webhook_secret"
        ]
    }


@router.get("/health")
async def webhook_health_check():
    """
    Health check endpoint for webhook service.
    """
    return {
        "status": "healthy",
        "service": "directus-webhooks",
        "timestamp": int(time.time()),
        "endpoints": [
            "/webhooks/directus/translate",
            "/webhooks/directus/validate", 
            "/webhooks/directus/test",
            "/webhooks/directus/info"
        ]
    }



# =============================================================================
# SCHEMA INTROSPECTION ENDPOINTS
# =============================================================================

# Schema introspection models
class DirectusSchemaRequest(BaseModel):
    """Request model for Directus schema introspection."""
    collection: str = Field(..., description="Collection name to introspect", min_length=1, max_length=100)
    client_id: str = Field(..., description="Client identifier", min_length=1, max_length=100)
    
    @validator('collection', 'client_id')
    def validate_required_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class DirectusSchemaResponse(BaseModel):
    """Response model for schema introspection."""
    collection: str
    schema: Dict[str, Any]
    suggested_translatable_fields: List[str]
    related_collections: List[Dict[str, str]]
    field_analysis: Dict[str, Any]
    recommendations: Dict[str, Any]


@router.post("/directus/schema/introspect", response_model=DirectusSchemaResponse)
async def introspect_collection_schema(
    request: DirectusSchemaRequest,
    db: Session = Depends(get_db)
):
    """
    Introspect a Directus collection schema to identify translatable fields.
    
    This endpoint analyzes a collection's schema and provides intelligent
    suggestions for which fields should be translated based on:
    - Field types (string, text, json)
    - Field interfaces (rich text editors, text inputs)
    - Field names (title, description, content, etc.)
    - Existing field configurations
    
    **Returns:**
    - Complete schema information
    - Suggested translatable fields
    - Related collections and their relationships
    - Field analysis and recommendations
    """
    try:
        # Mock schema data for now - in production this would connect to Directus API
        mock_schema = {
            "collection": request.collection,
            "fields": [
                {
                    "field": "id",
                    "type": "integer",
                    "interface": "input",
                    "primary_key": True,
                    "nullable": False
                },
                {
                    "field": "title",
                    "type": "string",
                    "interface": "input",
                    "length": 255,
                    "nullable": False
                },
                {
                    "field": "description",
                    "type": "text",
                    "interface": "input-rich-text-md",
                    "nullable": True
                },
                {
                    "field": "content",
                    "type": "json",
                    "interface": "input-rich-text-html",
                    "nullable": True
                },
                {
                    "field": "slug",
                    "type": "string",
                    "interface": "input",
                    "length": 255,
                    "nullable": False
                },
                {
                    "field": "status",
                    "type": "string",
                    "interface": "select-dropdown",
                    "options": ["draft", "published", "archived"],
                    "nullable": False
                },
                {
                    "field": "category_id",
                    "type": "integer",
                    "interface": "select-dropdown-m2o",
                    "relation": {
                        "collection": "categories",
                        "field": "id"
                    },
                    "nullable": True
                },
                {
                    "field": "author",
                    "type": "json",
                    "interface": "input-code",
                    "nullable": True
                },
                {
                    "field": "metadata",
                    "type": "json",
                    "interface": "input-code",
                    "nullable": True
                },
                {
                    "field": "created_at",
                    "type": "timestamp",
                    "interface": "datetime",
                    "nullable": False
                },
                {
                    "field": "updated_at",
                    "type": "timestamp",
                    "interface": "datetime",
                    "nullable": True
                }
            ],
            "meta": {
                "collection": request.collection,
                "icon": "article",
                "note": "Articles collection with translatable content",
                "display_template": "{{title}}",
                "hidden": False,
                "singleton": False,
                "translations": []
            }
        }
        
        # Analyze fields for translatability
        field_mapper = FieldMapper(db)
        
        # Get existing field configuration if any
        existing_config = await field_mapper.get_field_config(
            request.client_id, 
            request.collection
        )
        
        # Identify translatable fields based on type and interface
        translatable_fields = []
        field_analysis = {}
        
        translatable_types = ["string", "text", "json"]
        translatable_interfaces = [
            "input", "input-rich-text-md", "input-rich-text-html", 
            "textarea", "wysiwyg", "input-multiline"
        ]
        
        # Common field names that typically contain translatable content
        translatable_field_names = [
            "title", "name", "description", "content", "body", "summary",
            "excerpt", "bio", "about", "intro", "caption", "alt_text",
            "meta_title", "meta_description", "seo_title", "seo_description"
        ]
        
        for field in mock_schema["fields"]:
            field_name = field["field"]
            field_type = field["type"]
            field_interface = field.get("interface", "")
            
            # Skip system fields
            if field_name in ["id", "created_at", "updated_at", "status", "sort"]:
                field_analysis[field_name] = {
                    "translatable": False,
                    "reason": "System field",
                    "confidence": 0
                }
                continue
                
            # Skip primary keys and foreign keys
            if field.get("primary_key") or field_name.endswith("_id"):
                field_analysis[field_name] = {
                    "translatable": False,
                    "reason": "Key field",
                    "confidence": 0
                }
                continue
            
            # Calculate translatability score
            score = 0
            reasons = []
            
            # Type-based scoring
            if field_type in translatable_types:
                score += 30
                reasons.append(f"Translatable type: {field_type}")
            
            # Interface-based scoring
            if field_interface in translatable_interfaces:
                score += 40
                reasons.append(f"Text input interface: {field_interface}")
            
            # Name-based scoring
            if any(name in field_name.lower() for name in translatable_field_names):
                score += 50
                reasons.append("Common translatable field name")
            
            # Special handling for JSON fields
            if field_type == "json":
                if "rich-text" in field_interface:
                    score += 30
                    reasons.append("Rich text JSON field")
                elif field_name in ["content", "body", "description"]:
                    score += 20
                    reasons.append("Content JSON field")
                else:
                    score -= 10
                    reasons.append("Generic JSON field")
            
            # Length considerations for string fields
            if field_type == "string" and field.get("length", 0) > 50:
                score += 10
                reasons.append("Long string field")
            
            is_translatable = score >= 50
            confidence = min(score / 100.0, 1.0)
            
            field_analysis[field_name] = {
                "translatable": is_translatable,
                "score": score,
                "confidence": confidence,
                "reasons": reasons,
                "type": field_type,
                "interface": field_interface
            }
            
            if is_translatable:
                translatable_fields.append(field_name)
        
        # Identify related collections
        related_collections = []
        for field in mock_schema["fields"]:
            if field.get("relation") and field["relation"].get("collection"):
                related_collections.append({
                    "field": field["field"],
                    "collection": field["relation"]["collection"],
                    "type": "many_to_one"
                })
        
        # Generate recommendations
        recommendations = {
            "suggested_field_paths": translatable_fields,
            "batch_processing": len(translatable_fields) > 2,
            "preserve_html_structure": any(
                "rich-text" in field.get("interface", "") 
                for field in mock_schema["fields"]
            ),
            "rtl_support_needed": True,  # Always recommend RTL for Arabic/Bosnian
            "translation_pattern": "collection_translations",
            "priority_fields": [
                field for field, analysis in field_analysis.items()
                if analysis.get("confidence", 0) > 0.8
            ],
            "optional_fields": [
                field for field, analysis in field_analysis.items()
                if 0.5 <= analysis.get("confidence", 0) <= 0.8
            ],
            "field_types": {
                field: analysis["type"] 
                for field, analysis in field_analysis.items()
                if analysis.get("translatable", False)
            }
        }
        
        # Check if user already has configuration
        if existing_config.get("field_paths"):
            recommendations["existing_configuration"] = {
                "has_config": True,
                "current_fields": existing_config["field_paths"],
                "suggested_additions": [
                    field for field in translatable_fields 
                    if field not in existing_config["field_paths"]
                ],
                "suggested_removals": [
                    field for field in existing_config["field_paths"]
                    if field not in translatable_fields
                ]
            }
        else:
            recommendations["existing_configuration"] = {
                "has_config": False,
                "setup_needed": True
            }
        
        return DirectusSchemaResponse(
            collection=request.collection,
            schema=mock_schema,
            suggested_translatable_fields=translatable_fields,
            related_collections=related_collections,
            field_analysis=field_analysis,
            recommendations=recommendations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Schema introspection error: {str(e)}"
        ) from e


@router.post("/directus/schema/configure")
async def auto_configure_collection(
    request: DirectusSchemaRequest,
    db: Session = Depends(get_db)
):
    """
    Automatically configure field mapping based on schema introspection.
    
    This endpoint:
    1. Introspects the collection schema
    2. Identifies translatable fields automatically
    3. Creates a field configuration with optimal settings
    4. Returns the created configuration
    """
    try:
        # First, introspect the schema
        introspection_result = await introspect_collection_schema(request, db)
        
        # Create field configuration based on recommendations
        field_mapper = FieldMapper(db)
        
        recommendations = introspection_result.recommendations
        
        # Prepare field configuration
        field_config_data = {
            "field_paths": recommendations["suggested_field_paths"],
            "field_types": recommendations["field_types"],
            "batch_processing": recommendations["batch_processing"],
            "preserve_html_structure": recommendations["preserve_html_structure"],
            "directus_translation_pattern": recommendations["translation_pattern"]
        }
        
        # Save the configuration
        result = await field_mapper.save_field_config(request.client_id, request.collection, field_config_data)
        
        return {
            "success": True,
            "message": f"Auto-configured field mapping for collection '{request.collection}'",
            "configuration": result,
            "introspection": {
                "total_fields_analyzed": len(introspection_result.field_analysis),
                "translatable_fields_found": len(introspection_result.suggested_translatable_fields),
                "related_collections": len(introspection_result.related_collections),
                "confidence_distribution": {
                    "high": len(recommendations["priority_fields"]),
                    "medium": len(recommendations["optional_fields"]),
                    "low": len(introspection_result.suggested_translatable_fields) - 
                           len(recommendations["priority_fields"]) - 
                           len(recommendations["optional_fields"])
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Auto-configuration error: {str(e)}"
        ) from e


@router.get("/directus/schema/collections")
async def list_available_collections(
    client_id: str,
    db: Session = Depends(get_db)
):
    """
    List all available collections for a client.
    
    In production, this would connect to the Directus API to fetch
    all collections. For now, returns mock data.
    """
    try:
        # Mock collection data - in production this would come from Directus API
        mock_collections = [
            {
                "collection": "articles",
                "meta": {
                    "icon": "article",
                    "note": "Blog articles and posts",
                    "display_template": "{{title}}",
                    "field_count": 11
                },
                "configured": True,
                "translatable_fields": 3
            },
            {
                "collection": "pages",
                "meta": {
                    "icon": "pages",
                    "note": "Static pages content",
                    "display_template": "{{title}}",
                    "field_count": 8
                },
                "configured": False,
                "translatable_fields": 0
            },
            {
                "collection": "products",
                "meta": {
                    "icon": "shopping_cart",
                    "note": "E-commerce products",
                    "display_template": "{{name}} - {{price}}",
                    "field_count": 15
                },
                "configured": False,
                "translatable_fields": 0
            },
            {
                "collection": "categories",
                "meta": {
                    "icon": "folder",
                    "note": "Content categories",
                    "display_template": "{{name}}",
                    "field_count": 5
                },
                "configured": False,
                "translatable_fields": 0
            }
        ]
        
        # Check which collections have existing field configurations
        field_mapper = FieldMapper(db)
        
        for collection in mock_collections:
            existing_config = await field_mapper.get_field_config(
                client_id, 
                collection["collection"]
            )
            
            if existing_config.get("field_paths"):
                collection["configured"] = True
                collection["translatable_fields"] = len(existing_config["field_paths"])
                collection["last_updated"] = existing_config.get("updated_at")
            else:
                collection["configured"] = False
                collection["translatable_fields"] = 0
        
        return {
            "success": True,
            "collections": mock_collections,
            "total": len(mock_collections),
            "configured_count": sum(1 for c in mock_collections if c["configured"]),
            "unconfigured_count": sum(1 for c in mock_collections if not c["configured"])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Collections listing error: {str(e)}"
        ) from e



# =============================================================================
# COLLECTION RELATIONSHIPS ENDPOINTS
# =============================================================================

# Relationship models
class RelationshipTranslationRequest(BaseModel):
    """Request model for translating content with relationships."""
    content: Dict[str, Any] = Field(..., description="Content to translate")
    client_id: str = Field(..., description="Client identifier", min_length=1, max_length=100)
    collection: str = Field(..., description="Collection name", min_length=1, max_length=100)
    target_language: str = Field(..., description="Target language code")
    provider: str = Field(..., description="AI provider")
    api_key: str = Field(..., description="API key", min_length=10)
    source_language: str = Field(default="en", description="Source language code")
    max_depth: int = Field(default=3, description="Maximum relationship traversal depth", ge=1, le=10)
    translate_related: bool = Field(default=True, description="Whether to translate related items")
    
    @validator('target_language', 'source_language')
    def validate_language_codes(cls, v):
        if not v or len(v.strip()) != 2:
            raise ValueError("Language codes must be 2 characters long")
        return v.lower().strip()

    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = ["openai", "anthropic", "mistral", "deepseek"]
        if not v or v.lower().strip() not in valid_providers:
            raise ValueError(f"Provider must be one of: {valid_providers}")
        return v.lower().strip()

    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("API key must be at least 10 characters long")
        import re
        cleaned_key = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        if re.search(r'(?i)(system|user|assistant)\s*:', cleaned_key):
            raise ValueError("Invalid API key format")
        return cleaned_key.strip()

    @validator('client_id', 'collection')
    def validate_required_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @validator('content')
    def validate_content(cls, v):
        if not v or not isinstance(v, dict):
            raise ValueError("Content must be a valid JSON object")
        return v


class RelationshipAnalysisRequest(BaseModel):
    """Request model for analyzing collection relationships."""
    collection: str = Field(..., description="Collection name to analyze", min_length=1, max_length=100)
    max_depth: int = Field(default=5, description="Maximum analysis depth", ge=1, le=20)
    
    @validator('collection')
    def validate_collection(cls, v):
        if not v or not v.strip():
            raise ValueError("Collection name cannot be empty")
        return v.strip()


@router.post("/directus/relationships/translate")
async def translate_with_relationships(
    request: RelationshipTranslationRequest,
    db: Session = Depends(get_db)
):
    """
    Translate content including all related collections.
    
    This endpoint handles complex Directus collection relationships:
    - Many-to-one relationships (foreign keys)
    - One-to-many relationships (reverse foreign keys) 
    - Many-to-many relationships (junction tables)
    - Circular reference prevention
    - Configurable traversal depth
    
    **Features:**
    - Automatic relationship detection and traversal
    - Circular reference prevention
    - Configurable maximum depth to prevent performance issues
    - Selective translation of related items
    - Maintains relationship structure in translated output
    
    **Example Request:**
    ```json
    {
        "content": {
            "id": 1,
            "title": "Article Title",
            "category_id": {"id": 1, "name": "Technology"},
            "tags": [{"id": 1, "name": "AI"}, {"id": 2, "name": "Translation"}]
        },
        "client_id": "my_client",
        "collection": "articles",
        "target_language": "ar",
        "provider": "openai",
        "api_key": "sk-...",
        "max_depth": 2,
        "translate_related": true
    }
    ```
    """
    try:
        start_time = time.time()
        
        # Initialize services
        integrated_service = IntegratedTranslationService(db)
        field_mapper = FieldMapper(db)
        
        # Import the relationship service
        from ..services.relationship_handler import RelationshipAwareTranslationService
        relationship_service = RelationshipAwareTranslationService(field_mapper, integrated_service)
        
        # Perform relationship-aware translation
        result = await relationship_service.translate_with_relationships(
            content=request.content,
            client_id=request.client_id,
            collection_name=request.collection,
            source_lang=request.source_language,
            target_lang=request.target_language,
            provider=request.provider,
            api_key=request.api_key,
            max_depth=request.max_depth,
            translate_related=request.translate_related
        )
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            "success": True,
            "data": result,
            "metadata": {
                "processing_time_ms": processing_time,
                "collection": request.collection,
                "source_language": request.source_language,
                "target_language": request.target_language,
                "provider": request.provider,
                "max_depth": request.max_depth,
                "translate_related": request.translate_related,
                "timestamp": int(time.time())
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Relationship translation error: {str(e)}",
            "metadata": {
                "processing_time_ms": round((time.time() - start_time) * 1000, 2) if 'start_time' in locals() else 0,
                "collection": request.collection,
                "error_type": "relationship_translation_error"
            }
        }


@router.post("/directus/relationships/analyze")
async def analyze_collection_relationships(
    request: RelationshipAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze the complexity of collection relationships.
    
    This endpoint analyzes a collection's relationship structure and provides:
    - Relationship type distribution (many-to-one, one-to-many, etc.)
    - Maximum relationship depth
    - Circular reference detection
    - Complexity scoring
    - Performance recommendations
    
    **Use Cases:**
    - Planning translation strategies for complex schemas
    - Identifying performance bottlenecks
    - Detecting circular references before translation
    - Optimizing relationship traversal settings
    
    **Returns:**
    - Detailed relationship analysis
    - Complexity score (0-500+)
    - Performance recommendations
    - Circular reference warnings
    """
    try:
        # Initialize services
        integrated_service = IntegratedTranslationService(db)
        field_mapper = FieldMapper(db)
        
        # Import the relationship service
        from ..services.relationship_handler import RelationshipAwareTranslationService
        relationship_service = RelationshipAwareTranslationService(field_mapper, integrated_service)
        
        # Analyze relationships
        analysis = await relationship_service.analyze_collection_relationships(
            collection=request.collection,
            max_depth=request.max_depth
        )
        
        return {
            "success": True,
            "data": analysis,
            "metadata": {
                "collection": request.collection,
                "max_depth": request.max_depth,
                "timestamp": int(time.time())
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Relationship analysis error: {str(e)}",
            "metadata": {
                "collection": request.collection,
                "error_type": "relationship_analysis_error"
            }
        }


@router.get("/directus/relationships/info")
async def get_relationships_info():
    """
    Get information about relationship handling capabilities.
    
    Returns documentation and examples for using relationship-aware translation.
    """
    return {
        "relationships_endpoint": "/api/v1/webhooks/directus/relationships/translate",
        "analysis_endpoint": "/api/v1/webhooks/directus/relationships/analyze",
        "supported_relationship_types": [
            {
                "type": "many_to_one",
                "description": "Foreign key relationships (article -> category)",
                "example": "articles.category_id -> categories.id"
            },
            {
                "type": "one_to_many", 
                "description": "Reverse foreign key relationships (category -> articles)",
                "example": "categories.id <- articles.category_id"
            },
            {
                "type": "many_to_many",
                "description": "Junction table relationships (articles <-> tags)",
                "example": "articles <-> articles_tags <-> tags"
            },
            {
                "type": "one_to_one",
                "description": "Unique foreign key relationships",
                "example": "users.profile_id -> profiles.id"
            }
        ],
        "features": [
            "Automatic relationship detection and traversal",
            "Circular reference prevention",
            "Configurable maximum depth (1-10 levels)",
            "Selective translation of related items",
            "Relationship structure preservation",
            "Performance optimization recommendations"
        ],
        "complexity_scoring": {
            "low": "0-50: Simple relationships, standard settings recommended",
            "medium": "51-150: Moderate complexity, limit depth to 2-3 levels",
            "high": "151+: High complexity, limit depth to 1-2 levels"
        },
        "example_request": {
            "content": {
                "id": 1,
                "title": "Sample Article",
                "category_id": {"id": 1, "name": "Technology"},
                "tags": [{"id": 1, "name": "AI"}]
            },
            "client_id": "test_client",
            "collection": "articles",
            "target_language": "ar",
            "provider": "openai",
            "api_key": "sk-...",
            "max_depth": 2
        },
        "best_practices": [
            "Start with max_depth=1 for testing",
            "Use relationship analysis before bulk translation",
            "Monitor processing times with complex relationships",
            "Consider selective translation for large datasets",
            "Enable circular reference detection for self-referencing collections"
        ]
    }



# =============================================================================
# MIGRATION TOOLS ENDPOINTS
# =============================================================================

# Migration models
class MigrationExportRequest(BaseModel):
    """Request model for exporting translation configurations."""
    client_id: str = Field(..., description="Client identifier", min_length=1, max_length=100)
    collections: Optional[List[str]] = Field(None, description="Specific collections to export (all if not specified)")
    include_metadata: bool = Field(default=True, description="Include configuration metadata")
    format: str = Field(default="json", description="Export format")
    
    @validator('client_id')
    def validate_client_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Client ID cannot be empty")
        return v.strip()

    @validator('format')
    def validate_format(cls, v):
        valid_formats = ["json", "yaml", "csv"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Format must be one of: {valid_formats}")
        return v.lower()

    @validator('collections')
    def validate_collections(cls, v):
        if v is not None:
            return [col.strip() for col in v if col.strip()]
        return v


class MigrationImportRequest(BaseModel):
    """Request model for importing translation configurations."""
    client_id: str = Field(..., description="Target client identifier", min_length=1, max_length=100)
    configurations: List[Dict[str, Any]] = Field(..., description="Configuration data to import")
    overwrite_existing: bool = Field(default=False, description="Whether to overwrite existing configurations")
    validate_only: bool = Field(default=False, description="Only validate without importing")
    backup_existing: bool = Field(default=True, description="Backup existing configurations before import")
    
    @validator('client_id')
    def validate_client_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Client ID cannot be empty")
        return v.strip()

    @validator('configurations')
    def validate_configurations(cls, v):
        if not v or not isinstance(v, list):
            raise ValueError("Configurations must be a non-empty list")
        
        for i, config in enumerate(v):
            if not isinstance(config, dict):
                raise ValueError(f"Configuration {i} must be a dictionary")
            
            required_fields = ["collection_name", "field_paths"]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Configuration {i} missing required field: {field}")
        
        return v


class MigrationBatchRequest(BaseModel):
    """Request model for batch migration operations."""
    source_client_id: str = Field(..., description="Source client identifier", min_length=1, max_length=100)
    target_client_id: str = Field(..., description="Target client identifier", min_length=1, max_length=100)
    collections: Optional[List[str]] = Field(None, description="Specific collections to migrate")
    transformation_rules: Optional[Dict[str, Any]] = Field(None, description="Rules for transforming configurations during migration")
    
    @validator('source_client_id', 'target_client_id')
    def validate_client_ids(cls, v):
        if not v or not v.strip():
            raise ValueError("Client ID cannot be empty")
        return v.strip()


@router.post("/directus/migration/export")
async def export_translation_configurations(
    request: MigrationExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export translation configurations for backup or migration.
    
    This endpoint exports all or selected translation configurations for a client,
    including field mappings, translation patterns, and metadata.
    
    **Features:**
    - Export all configurations or specific collections
    - Multiple export formats (JSON, YAML, CSV)
    - Include/exclude metadata
    - Optimized for backup and migration workflows
    
    **Use Cases:**
    - Backup configurations before major changes
    - Migrate configurations between environments
    - Share configurations between clients
    - Version control for translation setups
    
    **Example Response:**
    ```json
    {
        "success": true,
        "data": {
            "client_id": "my_client",
            "exported_at": "2024-01-01T00:00:00Z",
            "version": "1.0",
            "configurations": [...]
        }
    }
    ```
    """
    try:
        from datetime import datetime
        
        field_mapper = FieldMapper(db)
        
        # Get all configurations for the client
        if request.collections:
            # Export specific collections
            configs = []
            for collection in request.collections:
                config = await field_mapper.get_field_config(request.client_id, collection)
                if config and config.get("field_paths"):
                    configs.append(config)
        else:
            # Export all configurations - we need to implement get_all_configs
            # For now, mock some data
            configs = [
                await field_mapper.get_field_config(request.client_id, "articles"),
                await field_mapper.get_field_config(request.client_id, "pages"),
                await field_mapper.get_field_config(request.client_id, "categories")
            ]
            # Filter out empty configs
            configs = [config for config in configs if config and config.get("field_paths")]
        
        # Prepare export data
        export_data = {
            "client_id": request.client_id,
            "exported_at": datetime.now().isoformat(),
            "version": "1.0",
            "format": request.format,
            "total_configurations": len(configs),
            "configurations": []
        }
        
        # Process each configuration
        for config in configs:
            if request.include_metadata:
                # Include full configuration with metadata
                export_config = {
                    "collection_name": config.get("collection_name"),
                    "field_paths": config.get("field_paths", []),
                    "field_types": config.get("field_types", {}),
                    "directus_translation_pattern": config.get("directus_translation_pattern"),
                    "batch_processing": config.get("batch_processing", False),
                    "preserve_html_structure": config.get("preserve_html_structure", True),
                    "content_sanitization": config.get("content_sanitization", True),
                    "rtl_field_mapping": config.get("rtl_field_mapping", {}),
                    "created_at": config.get("created_at"),
                    "updated_at": config.get("updated_at")
                }
            else:
                # Include only essential configuration
                export_config = {
                    "collection_name": config.get("collection_name"),
                    "field_paths": config.get("field_paths", []),
                    "field_types": config.get("field_types", {}),
                    "directus_translation_pattern": config.get("directus_translation_pattern", "collection_translations")
                }
            
            export_data["configurations"].append(export_config)
        
        # Format-specific processing
        if request.format == "json":
            response_data = export_data
        elif request.format == "yaml":
            import yaml
            yaml_content = yaml.dump(export_data, default_flow_style=False)
            response_data = {"yaml_content": yaml_content, "metadata": export_data}
        elif request.format == "csv":
            # Flatten configurations for CSV
            csv_data = []
            for config in export_data["configurations"]:
                csv_row = {
                    "collection_name": config["collection_name"],
                    "field_paths": ",".join(config.get("field_paths", [])),
                    "translation_pattern": config.get("directus_translation_pattern"),
                    "batch_processing": config.get("batch_processing", False)
                }
                csv_data.append(csv_row)
            response_data = {"csv_data": csv_data, "metadata": export_data}
        
        return {
            "success": True,
            "data": response_data,
            "metadata": {
                "export_format": request.format,
                "configurations_exported": len(configs),
                "timestamp": int(time.time())
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Export error: {str(e)}",
            "metadata": {
                "client_id": request.client_id,
                "error_type": "export_error"
            }
        }


@router.post("/directus/migration/import")
async def import_translation_configurations(
    request: MigrationImportRequest,
    db: Session = Depends(get_db)
):
    """
    Import translation configurations from backup or external source.
    
    This endpoint imports translation configurations, with options for:
    - Validation before import
    - Backing up existing configurations
    - Overwriting or merging with existing data
    - Batch processing for large imports
    
    **Features:**
    - Validation-only mode for testing
    - Automatic backup before overwrite
    - Conflict resolution strategies
    - Detailed import reporting
    - Rollback capabilities
    
    **Import Process:**
    1. Validate configuration format and structure
    2. Check for conflicts with existing configurations
    3. Backup existing configurations (if requested)
    4. Import new configurations
    5. Validate imported configurations
    6. Generate detailed import report
    """
    try:
        from datetime import datetime
        
        field_mapper = FieldMapper(db)
        
        # Validation phase
        validation_results = []
        for i, config in enumerate(request.configurations):
            validation_result = {
                "index": i,
                "collection_name": config.get("collection_name"),
                "valid": True,
                "warnings": [],
                "errors": []
            }
            
            # Check required fields
            required_fields = ["collection_name", "field_paths"]
            for field in required_fields:
                if field not in config or not config[field]:
                    validation_result["errors"].append(f"Missing required field: {field}")
                    validation_result["valid"] = False
            
            # Check field paths format
            if "field_paths" in config:
                if not isinstance(config["field_paths"], list):
                    validation_result["errors"].append("field_paths must be a list")
                    validation_result["valid"] = False
                elif len(config["field_paths"]) == 0:
                    validation_result["warnings"].append("field_paths is empty")
            
            # Check for existing configuration
            existing_config = await field_mapper.get_field_config(
                request.client_id, 
                config.get("collection_name")
            )
            
            if existing_config and existing_config.get("field_paths"):
                if request.overwrite_existing:
                    validation_result["warnings"].append("Will overwrite existing configuration")
                else:
                    validation_result["errors"].append("Configuration exists and overwrite_existing is False")
                    validation_result["valid"] = False
            
            validation_results.append(validation_result)
        
        # If validation-only mode, return validation results
        if request.validate_only:
            valid_count = sum(1 for r in validation_results if r["valid"])
            return {
                "success": True,
                "data": {
                    "validation_only": True,
                    "total_configurations": len(request.configurations),
                    "valid_configurations": valid_count,
                    "invalid_configurations": len(request.configurations) - valid_count,
                    "validation_results": validation_results
                },
                "metadata": {
                    "client_id": request.client_id,
                    "validation_timestamp": int(time.time())
                }
            }
        
        # Check if any configurations are invalid
        invalid_configs = [r for r in validation_results if not r["valid"]]
        if invalid_configs:
            return {
                "success": False,
                "error": "Invalid configurations found",
                "data": {
                    "invalid_configurations": len(invalid_configs),
                    "validation_results": validation_results
                },
                "metadata": {
                    "client_id": request.client_id,
                    "error_type": "validation_error"
                }
            }
        
        # Backup existing configurations if requested
        backup_data = None
        if request.backup_existing:
            backup_data = {
                "client_id": request.client_id,
                "backup_timestamp": datetime.now().isoformat(),
                "configurations": []
            }
            
            for config in request.configurations:
                collection_name = config.get("collection_name")
                existing = await field_mapper.get_field_config(request.client_id, collection_name)
                if existing and existing.get("field_paths"):
                    backup_data["configurations"].append(existing)
        
        # Import configurations
        import_results = []
        for i, config in enumerate(request.configurations):
            import_result = {
                "index": i,
                "collection_name": config.get("collection_name"),
                "success": False,
                "action": "none",
                "error": None
            }
            
            try:
                # Prepare configuration data
                field_config_data = {
                    "field_paths": config.get("field_paths", []),
                    "field_types": config.get("field_types", {}),
                    "directus_translation_pattern": config.get("directus_translation_pattern", "collection_translations"),
                    "batch_processing": config.get("batch_processing", False),
                    "preserve_html_structure": config.get("preserve_html_structure", True),
                    "content_sanitization": config.get("content_sanitization", True),
                    "rtl_field_mapping": config.get("rtl_field_mapping", {})
                }
                
                # Save configuration
                await field_mapper.save_field_config(
                    request.client_id,
                    config.get("collection_name"),
                    field_config_data
                )
                
                import_result["success"] = True
                import_result["action"] = "imported"
                
            except Exception as e:
                import_result["error"] = str(e)
            
            import_results.append(import_result)
        
        # Generate summary
        successful_imports = sum(1 for r in import_results if r["success"])
        failed_imports = len(import_results) - successful_imports
        
        return {
            "success": True,
            "data": {
                "import_summary": {
                    "total_configurations": len(request.configurations),
                    "successful_imports": successful_imports,
                    "failed_imports": failed_imports,
                    "backup_created": backup_data is not None
                },
                "import_results": import_results,
                "backup_data": backup_data,
                "validation_results": validation_results
            },
            "metadata": {
                "client_id": request.client_id,
                "import_timestamp": int(time.time()),
                "overwrite_existing": request.overwrite_existing
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Import error: {str(e)}",
            "metadata": {
                "client_id": request.client_id,
                "error_type": "import_error"
            }
        }


@router.post("/directus/migration/batch")
async def batch_migrate_configurations(
    request: MigrationBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Perform batch migration between clients or environments.
    
    This endpoint facilitates large-scale migration operations:
    - Copy configurations from source to target client
    - Apply transformation rules during migration
    - Selective collection migration
    - Conflict resolution
    
    **Use Cases:**
    - Environment promotion (dev → staging → production)
    - Client onboarding with template configurations
    - Bulk configuration updates
    - Cross-environment synchronization
    """
    try:
        field_mapper = FieldMapper(db)
        
        # Get source configurations
        source_configs = []
        if request.collections:
            for collection in request.collections:
                config = await field_mapper.get_field_config(request.source_client_id, collection)
                if config and config.get("field_paths"):
                    source_configs.append(config)
        else:
            # Get all configurations for source client (mock for now)
            collections = ["articles", "pages", "categories", "products"]
            for collection in collections:
                config = await field_mapper.get_field_config(request.source_client_id, collection)
                if config and config.get("field_paths"):
                    source_configs.append(config)
        
        if not source_configs:
            return {
                "success": False,
                "error": f"No configurations found for source client: {request.source_client_id}",
                "metadata": {
                    "source_client_id": request.source_client_id,
                    "target_client_id": request.target_client_id
                }
            }
        
        # Apply transformation rules if provided
        transformed_configs = []
        for config in source_configs:
            transformed_config = config.copy()
            
            if request.transformation_rules:
                rules = request.transformation_rules
                
                # Apply field path transformations
                if "field_path_mapping" in rules:
                    mapping = rules["field_path_mapping"]
                    new_paths = []
                    for path in transformed_config.get("field_paths", []):
                        new_path = mapping.get(path, path)
                        new_paths.append(new_path)
                    transformed_config["field_paths"] = new_paths
                
                # Apply pattern transformations
                if "pattern_mapping" in rules:
                    pattern_mapping = rules["pattern_mapping"]
                    current_pattern = transformed_config.get("directus_translation_pattern")
                    new_pattern = pattern_mapping.get(current_pattern, current_pattern)
                    transformed_config["directus_translation_pattern"] = new_pattern
                
                # Apply feature toggles
                if "feature_overrides" in rules:
                    overrides = rules["feature_overrides"]
                    for key, value in overrides.items():
                        if key in transformed_config:
                            transformed_config[key] = value
            
            transformed_configs.append(transformed_config)
        
        # Migrate configurations to target client
        migration_results = []
        for config in transformed_configs:
            result = {
                "collection_name": config.get("collection_name"),
                "success": False,
                "action": "none",
                "transformations_applied": bool(request.transformation_rules),
                "error": None
            }
            
            try:
                # Check if target already has this configuration
                existing = await field_mapper.get_field_config(
                    request.target_client_id,
                    config.get("collection_name")
                )
                
                if existing and existing.get("field_paths"):
                    result["action"] = "overwritten"
                else:
                    result["action"] = "created"
                
                # Prepare clean configuration data
                field_config_data = {
                    "field_paths": config.get("field_paths", []),
                    "field_types": config.get("field_types", {}),
                    "directus_translation_pattern": config.get("directus_translation_pattern", "collection_translations"),
                    "batch_processing": config.get("batch_processing", False),
                    "preserve_html_structure": config.get("preserve_html_structure", True),
                    "content_sanitization": config.get("content_sanitization", True),
                    "rtl_field_mapping": config.get("rtl_field_mapping", {})
                }
                
                # Save to target client
                await field_mapper.save_field_config(
                    request.target_client_id,
                    config.get("collection_name"),
                    field_config_data
                )
                
                result["success"] = True
                
            except Exception as e:
                result["error"] = str(e)
            
            migration_results.append(result)
        
        # Generate summary
        successful_migrations = sum(1 for r in migration_results if r["success"])
        failed_migrations = len(migration_results) - successful_migrations
        
        return {
            "success": True,
            "data": {
                "migration_summary": {
                    "source_client_id": request.source_client_id,
                    "target_client_id": request.target_client_id,
                    "total_configurations": len(source_configs),
                    "successful_migrations": successful_migrations,
                    "failed_migrations": failed_migrations,
                    "transformations_applied": bool(request.transformation_rules)
                },
                "migration_results": migration_results,
                "transformation_rules": request.transformation_rules
            },
            "metadata": {
                "source_client_id": request.source_client_id,
                "target_client_id": request.target_client_id,
                "migration_timestamp": int(time.time())
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Batch migration error: {str(e)}",
            "metadata": {
                "source_client_id": request.source_client_id,
                "target_client_id": request.target_client_id,
                "error_type": "batch_migration_error"
            }
        }


@router.get("/directus/migration/info")
async def get_migration_info():
    """
    Get information about migration tools and capabilities.
    
    Returns documentation and examples for using migration endpoints.
    """
    return {
        "migration_endpoints": {
            "export": "/api/v1/webhooks/directus/migration/export",
            "import": "/api/v1/webhooks/directus/migration/import",
            "batch": "/api/v1/webhooks/directus/migration/batch"
        },
        "supported_formats": ["json", "yaml", "csv"],
        "export_features": [
            "Full or selective configuration export",
            "Multiple export formats",
            "Metadata inclusion/exclusion",
            "Optimized for backup workflows"
        ],
        "import_features": [
            "Validation-only mode",
            "Automatic backup before import",
            "Conflict resolution",
            "Detailed import reporting",
            "Rollback capabilities"
        ],
        "batch_migration_features": [
            "Cross-client migration",
            "Configuration transformations",
            "Selective collection migration",
            "Environment promotion workflows"
        ],
        "transformation_rules": {
            "field_path_mapping": "Map old field paths to new ones",
            "pattern_mapping": "Transform translation patterns",
            "feature_overrides": "Override configuration features"
        },
        "example_export": {
            "client_id": "source_client",
            "collections": ["articles", "pages"],
            "include_metadata": True,
            "format": "json"
        },
        "example_import": {
            "client_id": "target_client",
            "configurations": ["..."],
            "overwrite_existing": False,
            "validate_only": False,
            "backup_existing": True
        },
        "example_batch_migration": {
            "source_client_id": "dev_client",
            "target_client_id": "prod_client",
            "collections": ["articles"],
            "transformation_rules": {
                "pattern_mapping": {
                    "collection_translations": "language_collections"
                }
            }
        },
        "best_practices": [
            "Always validate before importing",
            "Create backups before major operations",
            "Test transformations in development first",
            "Use selective migration for large datasets",
            "Monitor import results carefully"
        ]
    }
