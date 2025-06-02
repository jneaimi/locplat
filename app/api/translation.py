"""
Translation API endpoints for LocPlat service - Flexible provider/model selection.
"""
import time
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from ..services.flexible_translation_service import FlexibleTranslationService
from ..services import TranslationError, LanguageDirection

router = APIRouter(prefix="/translate", tags=["Translation"])

# Initialize the flexible translation service
translation_service = FlexibleTranslationService()


class FlexibleTranslationRequest(BaseModel):
    """Request model for flexible translation with provider/model selection."""
    text: str = Field(..., description="Text to translate", min_length=1, max_length=2000)
    source_lang: str = Field(..., description="Source language code (e.g., 'en')")
    target_lang: str = Field(..., description="Target language code (e.g., 'ar', 'bs')")
    provider: str = Field(
        ..., 
        description="AI provider ('openai', 'anthropic', 'mistral', 'deepseek')"
    )
    api_key: str = Field(
        ..., 
        description="API key for the specified provider", 
        min_length=10, 
        max_length=200
    )
    model: Optional[str] = Field(
        None, 
        description="Model name (optional, uses provider default)", 
        max_length=100
    )
    context: Optional[str] = Field(
        None, 
        description="Optional context for better translation", 
        max_length=500
    )

    @validator('source_lang', 'target_lang')
    def validate_language_codes(cls, v):
        """Validate language codes."""
        if len(v) != 2:
            raise ValueError("Language codes must be 2 characters long")
        return v.lower()

    @validator('provider')
    def validate_provider(cls, v):
        """Validate provider name."""
        valid_providers = ["openai", "anthropic", "mistral", "deepseek"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of: {valid_providers}")
        return v.lower()

    @validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key format and prevent common injection patterns."""
        import re
        # Remove any potential control characters
        cleaned_key = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        # Check for obvious injection attempts
        if re.search(r'(?i)(system|user|assistant)\s*:', cleaned_key):
            raise ValueError("Invalid API key format")
        return cleaned_key.strip()


class FlexibleBatchTranslationRequest(BaseModel):
    """Request model for flexible batch translation."""
    texts: List[str] = Field(
        ..., 
        description="List of texts to translate", 
        min_items=1, 
        max_items=50
    )
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code")
    provider: str = Field(..., description="AI provider name")
    api_key: str = Field(
        ..., 
        description="API key for the specified provider", 
        min_length=10, 
        max_length=200
    )
    model: Optional[str] = Field(
        None, 
        description="Model name (optional)", 
        max_length=100
    )
    context: Optional[str] = Field(
        None, 
        description="Optional context for better translation", 
        max_length=500
    )

    @validator('texts')
    def validate_texts(cls, v):
        """Validate texts list."""
        for text in v:
            if not text.strip():
                raise ValueError("All texts must be non-empty")
            if len(text) > 2000:  # Reduced from 10,000
                raise ValueError("Each text must be less than 2,000 characters")
        return v

    @validator('source_lang', 'target_lang')
    def validate_language_codes(cls, v):
        """Validate language codes."""
        if len(v) != 2:
            raise ValueError("Language codes must be 2 characters long")
        return v.lower()

    @validator('provider')
    def validate_provider(cls, v):
        """Validate provider name."""
        valid_providers = ["openai", "anthropic", "mistral", "deepseek"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of: {valid_providers}")
        return v.lower()

    @validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key format and prevent common injection patterns."""
        import re
        # Remove any potential control characters
        cleaned_key = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        # Check for obvious injection attempts
        if re.search(r'(?i)(system|user|assistant)\s*:', cleaned_key):
            raise ValueError("Invalid API key format")
        return cleaned_key.strip()


class TranslationResponse(BaseModel):
    """Response model for translation results."""
    translated_text: str
    provider_used: str
    model_used: str
    source_lang: str
    target_lang: str
    quality_score: float
    language_direction: str
    metadata: Dict[str, Any]


class BatchTranslationResponse(BaseModel):
    """Response model for batch translation results."""
    results: List[TranslationResponse]
    total_translations: int
    successful_translations: int
    provider_used: str
    model_used: str


class ProvidersResponse(BaseModel):
    """Response model for available providers and models."""
    providers: List[str]
    models: Dict[str, Dict[str, Any]]


class LanguagesResponse(BaseModel):
    """Response model for supported languages by provider."""
    provider: str
    languages: List[str]
    total_count: int


class LanguagePair(BaseModel):
    """Model for language pair information."""
    source: str
    target: str
    name: str
    supported_features: List[str] = Field(default_factory=list)
    quality_rating: str = "high"  # high, medium, low
    processing_time: str = "fast"  # fast, medium, slow


class EnhancedLanguagesResponse(BaseModel):
    """Enhanced response model for language pairs and capabilities."""
    provider: str
    models: Dict[str, Any]  # Changed to Any to handle both dict and string values
    language_pairs: List[LanguagePair]
    supported_features: List[str]
    total_pairs: int
    provider_info: Dict[str, Any]


class ServiceMetrics(BaseModel):
    """Response model for service metrics."""
    status: str
    uptime_seconds: float
    providers: Dict[str, Dict[str, Any]]
    cache_stats: Dict[str, Any]
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time_ms: float
    success_rate: float
    timestamp: float


class ValidationResponse(BaseModel):
    """Response model for API key validation."""
    provider: str
    is_valid: bool
    message: str


class TranslationRecord(BaseModel):
    """Model for translation history records."""
    id: str
    timestamp: float
    client_id: str
    source_language: str
    target_language: str
    provider: str
    model_used: str
    content_type: str  # "text", "batch", "structured"
    character_count: int
    processing_time_ms: float
    status: str  # "success", "failed", "cached"
    cache_hit: bool
    quality_score: Optional[float] = None
    error_message: Optional[str] = None


class TranslationHistoryRequest(BaseModel):
    """Request model for translation history filtering."""
    client_id: Optional[str] = Field(None, description="Filter by client ID")
    provider: Optional[str] = Field(None, description="Filter by provider")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")
    content_type: Optional[str] = Field(None, description="Filter by content type")
    status: Optional[str] = Field(None, description="Filter by status")
    limit: int = Field(100, description="Maximum records to return", ge=1, le=1000)
    offset: int = Field(0, description="Number of records to skip", ge=0)


class TranslationHistoryResponse(BaseModel):
    """Response model for translation history."""
    records: List[TranslationRecord]
    total_count: int
    limit: int
    offset: int
    has_more: bool


# Global metrics storage (in production, this would be in Redis or database)
_service_metrics = {
    "start_time": time.time(),
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "response_times": [],
    "provider_stats": {}
}


def record_request_metric(provider: str, success: bool, response_time_ms: float):
    """Record metrics for a request."""
    _service_metrics["total_requests"] += 1
    _service_metrics["response_times"].append(response_time_ms)
    
    # Keep only last 1000 response times to prevent memory issues
    if len(_service_metrics["response_times"]) > 1000:
        _service_metrics["response_times"] = _service_metrics["response_times"][-1000:]
    
    if success:
        _service_metrics["successful_requests"] += 1
    else:
        _service_metrics["failed_requests"] += 1
    
    # Provider-specific metrics
    if provider not in _service_metrics["provider_stats"]:
        _service_metrics["provider_stats"][provider] = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "response_times": []
        }
    
    provider_stats = _service_metrics["provider_stats"][provider]
    provider_stats["requests"] += 1
    provider_stats["response_times"].append(response_time_ms)
    
    # Keep only last 100 response times per provider
    if len(provider_stats["response_times"]) > 100:
        provider_stats["response_times"] = provider_stats["response_times"][-100:]
    
    if success:
        provider_stats["successes"] += 1
    else:
        provider_stats["failures"] += 1


# Global translation history storage (in production, this would be in database)
_translation_history = []


def record_translation(
    client_id: str,
    source_lang: str,
    target_lang: str,
    provider: str,
    model_used: str,
    content_type: str,
    character_count: int,
    processing_time_ms: float,
    status: str,
    cache_hit: bool = False,
    quality_score: Optional[float] = None,
    error_message: Optional[str] = None
):
    """Record a translation in the history."""
    import uuid
    
    record = TranslationRecord(
        id=str(uuid.uuid4()),
        timestamp=time.time(),
        client_id=client_id,
        source_language=source_lang,
        target_language=target_lang,
        provider=provider,
        model_used=model_used,
        content_type=content_type,
        character_count=character_count,
        processing_time_ms=processing_time_ms,
        status=status,
        cache_hit=cache_hit,
        quality_score=quality_score,
        error_message=error_message
    )
    
    _translation_history.append(record)
    
    # Keep only last 10,000 records to prevent memory issues
    if len(_translation_history) > 10000:
        _translation_history[:] = _translation_history[-10000:]



@router.post("/", response_model=TranslationResponse)
async def translate_text(request: FlexibleTranslationRequest):
    """
    Translate a single text using specified provider and model.
    """
    try:
        result = await translation_service.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            context=request.context
        )

        # Create response with RTL display enhancement
        language_direction = result.metadata.get("language_direction", "ltr")
        metadata = result.metadata.copy()
        
        # Add RTL display helpers for Arabic and other RTL languages
        if language_direction == "rtl":
            metadata["display_options"] = {
                "terminal_rtl": f"\u202E{result.translated_text}\u202C",
                "html_rtl": f'<div dir="rtl" style="text-align: right; direction: rtl;">{result.translated_text}</div>',
                "css_attributes": 'dir="rtl" style="text-align: right; direction: rtl;"'
            }

        return TranslationResponse(
            translated_text=result.translated_text,
            provider_used=result.provider_used,
            model_used=result.metadata.get("model_used", "default"),
            source_lang=result.source_lang,
            target_lang=result.target_lang,
            quality_score=result.quality_score,
            language_direction=language_direction,
            metadata=metadata
        )

    except TranslationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.post("/batch", response_model=BatchTranslationResponse)
async def translate_batch(request: FlexibleBatchTranslationRequest):
    """
    Translate multiple texts using specified provider and model.
    """
    try:
        results = await translation_service.batch_translate(
            texts=request.texts,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            context=request.context
        )

        response_results = []
        for result in results:
            language_direction = result.metadata.get("language_direction", "ltr")
            metadata = result.metadata.copy()
            
            # Add RTL display helpers for Arabic and other RTL languages
            if language_direction == "rtl":
                metadata["display_options"] = {
                    "terminal_rtl": f"\u202E{result.translated_text}\u202C",
                    "html_rtl": f'<div dir="rtl" style="text-align: right; direction: rtl;">{result.translated_text}</div>',
                    "css_attributes": 'dir="rtl" style="text-align: right; direction: rtl;"'
                }

            response_results.append(TranslationResponse(
                translated_text=result.translated_text,
                provider_used=result.provider_used,
                model_used=result.metadata.get("model_used", "default"),
                source_lang=result.source_lang,
                target_lang=result.target_lang,
                quality_score=result.quality_score,
                language_direction=language_direction,
                metadata=metadata
            ))

        return BatchTranslationResponse(
            results=response_results,
            total_translations=len(request.texts),
            successful_translations=len(results),
            provider_used=request.provider,
            model_used=request.model or "default"
        )

    except TranslationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e



@router.get("/providers", response_model=ProvidersResponse)
async def get_providers_and_models():
    """
    Get available providers and their supported models.
    """
    try:
        providers = translation_service.get_available_providers()
        models = translation_service.get_provider_models()

        return ProvidersResponse(
            providers=providers,
            models=models
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/languages/{provider}", response_model=LanguagesResponse)
async def get_supported_languages(provider: str):
    """
    Get supported languages for a specific provider.
    """
    try:
        available_providers = translation_service.get_available_providers()
        if provider not in available_providers:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider}' not found. Available: {available_providers}"
            )

        languages = translation_service.get_supported_languages(provider)

        return LanguagesResponse(
            provider=provider,
            languages=languages,
            total_count=len(languages)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/language-pairs/{provider}", response_model=EnhancedLanguagesResponse)
async def get_language_pairs_by_provider(provider: str):
    """
    Get detailed language pairs and capabilities for a specific provider.
    
    This enhanced endpoint provides comprehensive information about:
    - Supported language pairs with quality ratings
    - Available models and their characteristics
    - Provider-specific features and capabilities
    - Processing time estimates for different language pairs
    """
    try:
        available_providers = translation_service.get_available_providers()
        if provider not in available_providers:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider}' not found. Available: {available_providers}"
            )

        # Get basic language support
        languages = translation_service.get_supported_languages(provider)
        
        # Get provider models
        all_models = translation_service.get_provider_models()
        provider_models = all_models.get(provider, {})
        
        # Create language pairs
        language_pairs = []
        
        # Define supported pairs for each provider
        if provider == "openai":
            # OpenAI supports many language pairs, focus on project requirements
            primary_pairs = [
                ("en", "ar", "English to Arabic", ["structured", "batch", "html", "rtl"], "high", "fast"),
                ("en", "bs", "English to Bosnian", ["structured", "batch", "html"], "high", "fast"),
                ("ar", "en", "Arabic to English", ["structured", "batch", "html", "rtl"], "high", "fast"),
                ("bs", "en", "Bosnian to English", ["structured", "batch", "html"], "high", "fast"),
            ]
            
            # Add other common pairs
            for source in ["en", "ar", "bs"]:
                for target in languages:
                    if source != target and (source, target) not in [(s, t) for s, t, _, _, _, _ in primary_pairs]:
                        features = ["structured", "batch"]
                        if target == "ar":
                            features.append("rtl")
                        if source in ["en", "ar", "bs"] or target in ["en", "ar", "bs"]:
                            quality = "high"
                            speed = "fast"
                        else:
                            quality = "medium"
                            speed = "medium"
                        
                        language_pairs.append(LanguagePair(
                            source=source,
                            target=target,
                            name=f"{source.upper()} to {target.upper()}",
                            supported_features=features,
                            quality_rating=quality,
                            processing_time=speed
                        ))
            
            # Add primary pairs
            for source, target, name, features, quality, speed in primary_pairs:
                language_pairs.append(LanguagePair(
                    source=source,
                    target=target,
                    name=name,
                    supported_features=features,
                    quality_rating=quality,
                    processing_time=speed
                ))
                
        elif provider in ["anthropic", "mistral", "deepseek"]:
            # These providers have similar capabilities to OpenAI
            primary_pairs = [
                ("en", "ar", "English to Arabic", ["structured", "batch", "html", "rtl"], "high", "medium"),
                ("en", "bs", "English to Bosnian", ["structured", "batch", "html"], "high", "medium"),
                ("ar", "en", "Arabic to English", ["structured", "batch", "html", "rtl"], "high", "medium"),
                ("bs", "en", "Bosnian to English", ["structured", "batch", "html"], "high", "medium"),
            ]
            
            for source, target, name, features, quality, speed in primary_pairs:
                language_pairs.append(LanguagePair(
                    source=source,
                    target=target,
                    name=name,
                    supported_features=features,
                    quality_rating=quality,
                    processing_time=speed
                ))
        
        # Define provider-specific features
        provider_features = {
            "openai": ["structured_content", "batch_processing", "html_preservation", "rtl_support", "context_awareness", "fast_processing"],
            "anthropic": ["structured_content", "batch_processing", "html_preservation", "rtl_support", "context_awareness", "high_quality"],
            "mistral": ["structured_content", "batch_processing", "html_preservation", "european_languages", "fast_processing"],
            "deepseek": ["structured_content", "batch_processing", "html_preservation", "cost_effective", "reliable"]
        }
        
        # Provider information
        provider_info = {
            "openai": {
                "name": "OpenAI",
                "description": "High-quality translations with fast processing and excellent context understanding",
                "strengths": ["Context awareness", "Fast processing", "Wide language support"],
                "best_for": ["General translations", "Technical content", "RTL languages"]
            },
            "anthropic": {
                "name": "Anthropic Claude",
                "description": "Premium translations with excellent cultural sensitivity and nuanced understanding",
                "strengths": ["Cultural sensitivity", "Nuanced translations", "Context preservation"],
                "best_for": ["Cultural content", "Marketing materials", "Creative writing"]
            },
            "mistral": {
                "name": "Mistral AI",
                "description": "Efficient translations with strong European language support",
                "strengths": ["European languages", "Technical accuracy", "Consistent quality"],
                "best_for": ["European content", "Technical documentation", "Business translations"]
            },
            "deepseek": {
                "name": "DeepSeek",
                "description": "Cost-effective translations with reliable quality and good performance",
                "strengths": ["Cost efficiency", "Reliable quality", "Good performance"],
                "best_for": ["Large volumes", "Budget-conscious projects", "Consistent workflows"]
            }
        }

        return EnhancedLanguagesResponse(
            provider=provider,
            models=provider_models,
            language_pairs=language_pairs,
            supported_features=provider_features.get(provider, []),
            total_pairs=len(language_pairs),
            provider_info=provider_info.get(provider, {})
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


class ApiKeyValidationRequest(BaseModel):
    """Request model for API key validation."""
    api_key: str = Field(..., description="API key to validate", min_length=10, max_length=200)

    @validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key format and prevent common injection patterns."""
        import re
        # Remove any potential control characters
        cleaned_key = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        # Check for obvious injection attempts
        if re.search(r'(?i)(system|user|assistant)\s*:', cleaned_key):
            raise ValueError("Invalid API key format")
        return cleaned_key.strip()


@router.post("/validate/{provider}", response_model=ValidationResponse)
async def validate_api_key(provider: str, request: ApiKeyValidationRequest):
    """
    Validate an API key for a specific provider.
    """
    try:
        available_providers = translation_service.get_available_providers()
        if provider not in available_providers:
            raise HTTPException(
                status_code=404,
                detail=f"Provider '{provider}' not found. Available: {available_providers}"
            )

        is_valid = await translation_service.validate_api_key(provider, request.api_key)

        return ValidationResponse(
            provider=provider,
            is_valid=is_valid,
            message="API key is valid" if is_valid else "API key is invalid"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/language-direction/{lang_code}")
async def get_language_direction(lang_code: str):
    """
    Get text direction for a language code.
    """
    try:
        direction = translation_service.get_language_direction(lang_code)

        return {
            "language_code": lang_code.lower(),
            "direction": direction.value,
            "is_rtl": direction == LanguageDirection.RTL
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


# ==== NEW: Structured Content Translation Endpoints ====

class StructuredTranslationRequest(BaseModel):
    """Request model for structured content translation with field mapping."""
    content: Dict[str, Any] = Field(..., description="Structured content to translate")
    client_id: str = Field(..., description="Client identifier", min_length=1, max_length=100)
    collection_name: str = Field(..., description="Collection name for field mapping", min_length=1, max_length=100)
    source_lang: str = Field(..., description="Source language code (e.g., 'en')")
    target_lang: str = Field(..., description="Target language code (e.g., 'ar', 'bs')")
    provider: str = Field(..., description="AI provider ('openai', 'anthropic', 'mistral', 'deepseek')")
    api_key: str = Field(..., description="API key for the specified provider", min_length=10, max_length=200)
    model: Optional[str] = Field(None, description="Model name (optional, uses provider default)", max_length=100)
    context: Optional[str] = Field(None, description="Optional context for better translation", max_length=500)

    @validator('source_lang', 'target_lang')
    def validate_language_codes(cls, v):
        if len(v) != 2:
            raise ValueError("Language codes must be 2 characters long")
        return v.lower()

    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = ["openai", "anthropic", "mistral", "deepseek"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of: {valid_providers}")
        return v.lower()

    @validator('api_key')
    def validate_api_key(cls, v):
        import re
        cleaned_key = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        if re.search(r'(?i)(system|user|assistant)\s*:', cleaned_key):
            raise ValueError("Invalid API key format")
        return cleaned_key.strip()


class TranslationPreviewRequest(BaseModel):
    """Request model for translation preview."""
    content: Dict[str, Any] = Field(..., description="Content to preview")
    client_id: str = Field(..., description="Client identifier")
    collection_name: str = Field(..., description="Collection name")
    target_lang: str = Field(..., description="Target language code")

    @validator('target_lang')
    def validate_target_lang(cls, v):
        if len(v) != 2:
            raise ValueError("Language code must be 2 characters long")
        return v.lower()


class ValidationRequest(BaseModel):
    """Request model for translation validation."""
    client_id: str = Field(..., description="Client identifier")
    collection_name: str = Field(..., description="Collection name")
    provider: str = Field(..., description="AI provider")
    api_key: str = Field(..., description="API key for the provider")
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code")

    @validator('source_lang', 'target_lang')
    def validate_language_codes(cls, v):
        if len(v) != 2:
            raise ValueError("Language codes must be 2 characters long")
        return v.lower()

    @validator('provider')
    def validate_provider(cls, v):
        valid_providers = ["openai", "anthropic", "mistral", "deepseek"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Provider must be one of: {valid_providers}")
        return v.lower()


@router.post("/structured", summary="Translate structured content with field mapping")
async def translate_structured_content(request: StructuredTranslationRequest):
    """
    Translate structured content using field mapping configuration.
    
    This endpoint combines field mapping with AI translation to process structured content
    like Directus collections. It extracts translatable fields based on configuration,
    translates them using the specified provider, and reconstructs the content.
    
    **Key Features:**
    - Field mapping configuration per client/collection
    - Batch processing for efficiency
    - HTML structure preservation
    - Directus translation patterns
    - RTL language support
    """
    try:
        from ..database import get_db
        from ..services.integrated_translation_service import IntegratedTranslationService
        
        # Get database session
        db = next(get_db())
        
        # Initialize integrated service
        integrated_service = IntegratedTranslationService(db)
        
        # Perform structured translation
        result = await integrated_service.translate_structured_content(
            content=request.content,
            client_id=request.client_id,
            collection_name=request.collection_name,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            provider=request.provider,
            api_key=request.api_key,
            model=request.model,
            context=request.context
        )
        
        return {
            "success": True,
            "data": result
        }

    except TranslationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.post("/preview", summary="Preview translatable fields")
async def preview_translation(request: TranslationPreviewRequest):
    """
    Preview what fields would be translated without actually translating.
    
    This endpoint shows which fields will be extracted and translated based on
    the field mapping configuration for the specified client and collection.
    """
    try:
        from ..database import get_db
        from ..services.integrated_translation_service import IntegratedTranslationService
        
        db = next(get_db())
        integrated_service = IntegratedTranslationService(db)
        
        preview = await integrated_service.get_translation_preview(
            content=request.content,
            client_id=request.client_id,
            collection_name=request.collection_name,
            target_lang=request.target_lang
        )
        
        return {
            "success": True,
            "data": preview
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.post("/validate", summary="Validate translation request")
async def validate_translation_request(request: ValidationRequest):
    """
    Validate a translation request before processing.
    
    Checks:
    - Field mapping configuration exists
    - Provider is supported
    - API key is valid
    - Language pair is supported
    """
    try:
        from ..database import get_db
        from ..services.integrated_translation_service import IntegratedTranslationService
        
        db = next(get_db())
        integrated_service = IntegratedTranslationService(db)
        
        validation_result = await integrated_service.validate_translation_request(
            client_id=request.client_id,
            collection_name=request.collection_name,
            provider=request.provider,
            api_key=request.api_key,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
        
        return {
            "success": True,
            "data": validation_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/metrics", response_model=ServiceMetrics)
async def get_service_metrics():
    """
    Get comprehensive service metrics including performance, provider statistics, and cache information.
    
    **Metrics Included:**
    - Service uptime and overall health status
    - Request counts and success/failure rates
    - Average response times globally and per provider
    - Provider-specific statistics and availability
    - Cache performance metrics
    - Real-time system status
    
    **Use Cases:**
    - Service monitoring and alerting
    - Performance optimization analysis
    - Provider performance comparison
    - Cache efficiency tracking
    - SLA monitoring and reporting
    """
    try:
        import time
        from ..services.ai_response_cache import get_cache
        
        current_time = time.time()
        uptime = current_time - _service_metrics["start_time"]
        
        # Calculate average response time
        response_times = _service_metrics["response_times"]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate success rate
        total_requests = _service_metrics["total_requests"]
        success_rate = (_service_metrics["successful_requests"] / total_requests * 100) if total_requests > 0 else 100
        
        # Provider statistics
        provider_stats = {}
        available_providers = translation_service.get_available_providers()
        
        for provider in available_providers:
            provider_data = _service_metrics["provider_stats"].get(provider, {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "response_times": []
            })
            
            provider_response_times = provider_data["response_times"]
            provider_avg_time = sum(provider_response_times) / len(provider_response_times) if provider_response_times else 0
            provider_requests = provider_data["requests"]
            provider_success_rate = (provider_data["successes"] / provider_requests * 100) if provider_requests > 0 else 100
            
            provider_stats[provider] = {
                "available": True,  # In a real implementation, this would check actual provider availability
                "requests": provider_requests,
                "successes": provider_data["successes"],
                "failures": provider_data["failures"],
                "success_rate": round(provider_success_rate, 2),
                "average_response_time_ms": round(provider_avg_time, 2),
                "last_request": "recently" if provider_requests > 0 else "never"
            }
        
        # Get cache statistics
        try:
            cache = await get_cache()
            cache_stats = await cache.get_cache_info()
        except Exception:
            cache_stats = {
                "status": "unavailable",
                "error": "Could not retrieve cache statistics"
            }
        
        # Determine overall service status
        if success_rate > 95 and avg_response_time < 2000:
            status = "healthy"
        elif success_rate > 90 and avg_response_time < 5000:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return ServiceMetrics(
            status=status,
            uptime_seconds=round(uptime, 2),
            providers=provider_stats,
            cache_stats=cache_stats,
            total_requests=total_requests,
            successful_requests=_service_metrics["successful_requests"],
            failed_requests=_service_metrics["failed_requests"],
            average_response_time_ms=round(avg_response_time, 2),
            success_rate=round(success_rate, 2),
            timestamp=current_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/history", response_model=TranslationHistoryResponse)
async def get_translation_history(
    client_id: Optional[str] = None,
    provider: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get translation history with filtering and pagination support.
    
    **Query Parameters:**
    - `client_id`: Filter by specific client
    - `provider`: Filter by AI provider (openai, anthropic, mistral, deepseek)
    - `start_date`: Filter by start date (ISO format: 2024-01-01T00:00:00Z)
    - `end_date`: Filter by end date (ISO format: 2024-12-31T23:59:59Z)
    - `content_type`: Filter by content type (text, batch, structured)
    - `status`: Filter by translation status (success, failed, cached)
    - `limit`: Maximum records to return (1-1000, default: 100)
    - `offset`: Number of records to skip for pagination (default: 0)
    
    **Use Cases:**
    - Audit trail for translation activities
    - Performance analysis and optimization
    - Client usage tracking and billing
    - Error analysis and debugging
    - Cost analysis per client/provider
    
    **Response includes:**
    - Paginated translation records
    - Total count for pagination
    - Detailed metadata for each translation
    """
    try:
        from datetime import datetime
        
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
        if offset < 0:
            raise HTTPException(status_code=400, detail="offset must be non-negative")
        
        # Parse date filters
        start_timestamp = None
        end_timestamp = None
        
        if start_date:
            try:
                start_timestamp = datetime.fromisoformat(start_date.replace('Z', '+00:00')).timestamp()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format: 2024-01-01T00:00:00Z")
        
        if end_date:
            try:
                end_timestamp = datetime.fromisoformat(end_date.replace('Z', '+00:00')).timestamp()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format: 2024-12-31T23:59:59Z")
        
        # Filter records
        filtered_records = []
        for record in _translation_history:
            # Apply filters
            if client_id and record.client_id != client_id:
                continue
            if provider and record.provider != provider:
                continue
            if start_timestamp and record.timestamp < start_timestamp:
                continue
            if end_timestamp and record.timestamp > end_timestamp:
                continue
            if content_type and record.content_type != content_type:
                continue
            if status and record.status != status:
                continue
            
            filtered_records.append(record)
        
        # Sort by timestamp (newest first)
        filtered_records.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        total_count = len(filtered_records)
        paginated_records = filtered_records[offset:offset + limit]
        has_more = (offset + limit) < total_count
        
        return TranslationHistoryResponse(
            records=paginated_records,
            total_count=total_count,
            limit=limit,
            offset=offset,
            has_more=has_more
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e
