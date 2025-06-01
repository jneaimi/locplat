"""
Translation API endpoints for LocPlat service - Flexible provider/model selection.
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from ..services.flexible_translation_service import FlexibleTranslationService
from ..services import TranslationError, LanguageDirection

router = APIRouter(prefix="/translate", tags=["translation"])

# Initialize the flexible translation service
translation_service = FlexibleTranslationService()


class FlexibleTranslationRequest(BaseModel):
    """Request model for flexible translation with provider/model selection."""
    text: str = Field(..., description="Text to translate", min_length=1, max_length=10000)
    source_lang: str = Field(..., description="Source language code (e.g., 'en')")
    target_lang: str = Field(..., description="Target language code (e.g., 'ar', 'bs')")
    provider: str = Field(..., description="AI provider ('openai', 'anthropic', 'mistral', 'deepseek')")
    api_key: str = Field(..., description="API key for the specified provider")
    model: Optional[str] = Field(None, description="Model name (optional, uses provider default)")
    context: Optional[str] = Field(None, description="Optional context for better translation")
    
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


class FlexibleBatchTranslationRequest(BaseModel):
    """Request model for flexible batch translation."""
    texts: List[str] = Field(..., description="List of texts to translate", min_items=1, max_items=100)
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code") 
    provider: str = Field(..., description="AI provider name")
    api_key: str = Field(..., description="API key for the specified provider")
    model: Optional[str] = Field(None, description="Model name (optional)")
    context: Optional[str] = Field(None, description="Optional context for better translation")
    
    @validator('texts')
    def validate_texts(cls, v):
        """Validate texts list."""
        for text in v:
            if not text.strip():
                raise ValueError("All texts must be non-empty")
            if len(text) > 10000:
                raise ValueError("Each text must be less than 10,000 characters")
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


class ValidationResponse(BaseModel):
    """Response model for API key validation."""
    provider: str
    is_valid: bool
    message: str



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
        
        return TranslationResponse(
            translated_text=result.translated_text,
            provider_used=result.provider_used,
            model_used=result.metadata.get("model_used", "default"),
            source_lang=result.source_lang,
            target_lang=result.target_lang,
            quality_score=result.quality_score,
            language_direction=result.metadata.get("language_direction", "ltr"),
            metadata=result.metadata
        )
        
    except TranslationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
        
        response_results = [
            TranslationResponse(
                translated_text=result.translated_text,
                provider_used=result.provider_used,
                model_used=result.metadata.get("model_used", "default"),
                source_lang=result.source_lang,
                target_lang=result.target_lang,
                quality_score=result.quality_score,
                language_direction=result.metadata.get("language_direction", "ltr"),
                metadata=result.metadata
            )
            for result in results
        ]
        
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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class ApiKeyValidationRequest(BaseModel):
    """Request model for API key validation."""
    api_key: str = Field(..., description="API key to validate")


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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
