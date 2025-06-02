"""
Webhook API endpoints for Directus CMS integration - Automatic content translation.
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
        if v and len(v) != 2:
            raise ValueError("Language codes must be 2 characters long")
        return v.lower() if v else v

    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = ["openai", "anthropic", "mistral", "deepseek"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of: {valid_providers}")
        return v.lower()

    @validator('event')
    def validate_event(cls, v):
        valid_events = [
            "items.create", "items.update", "items.delete",
            "flow.operation", "custom.translate"
        ]
        if v not in valid_events:
            raise ValueError(f"Event must be one of: {valid_events}")
        return v

    @validator('api_key')
    def validate_api_key(cls, v):
        import re
        cleaned_key = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        if re.search(r'(?i)(system|user|assistant)\s*:', cleaned_key):
            raise ValueError("Invalid API key format")
        return cleaned_key.strip()


class DirectusWebhookResponse(BaseModel):
    """Response model for Directus webhook."""
    success: bool
    operation: str  # "insert", "update", "skip"
    collection: str
    translated_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebhookValidationRequest(BaseModel):
    """Request model for webhook validation."""
    client_id: str = Field(..., description="Client identifier")
    collection: str = Field(..., description="Collection name")
    provider: str = Field(..., description="AI provider")
    api_key: str = Field(..., description="API key")
    target_language: str = Field(..., description="Target language code")
    
    @validator('target_language')
    def validate_target_language(cls, v):
        if len(v) != 2:
            raise ValueError("Language code must be 2 characters long")
        return v.lower()

    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = ["openai", "anthropic", "mistral", "deepseek"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of: {valid_providers}")
        return v.lower()


class WebhookTestRequest(BaseModel):
    """Request model for webhook testing."""
    sample_data: Dict[str, Any] = Field(..., description="Sample content data")
    client_id: str = Field(..., description="Client identifier")
    collection: str = Field(..., description="Collection name")
    target_language: str = Field(..., description="Target language code")
    provider: str = Field(..., description="AI provider")
    api_key: str = Field(..., description="API key")
    dry_run: bool = Field(True, description="Whether to perform actual translation")


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
    Validate webhook configuration before setting up in Directus.
    
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
                "client_id": request.client_id,
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
    Test webhook processing with sample data.
    
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
