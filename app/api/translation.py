"""
Translation API endpoints for LocPlat service.
"""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from ..services import ProviderRouter, TranslationError, LanguageDirection

router = APIRouter(prefix="/translate", tags=["translation"])

# Initialize the provider router
provider_router = ProviderRouter()


class TranslationRequest(BaseModel):
    """Request model for single text translation."""
    text: str = Field(..., description="Text to translate", min_length=1, max_length=10000)
    source_lang: str = Field(..., description="Source language code (e.g., 'en')")
    target_lang: str = Field(..., description="Target language code (e.g., 'ar', 'bs')")
    context: Optional[str] = Field(None, description="Optional context for better translation")
    api_keys: Dict[str, str] = Field(..., description="Provider API keys")
    
    @validator('source_lang', 'target_lang')
    def validate_language_codes(cls, v):
        """Validate language codes."""
        if len(v) != 2:
            raise ValueError("Language codes must be 2 characters long")
        return v.lower()
    
    @validator('api_keys')
    def validate_api_keys(cls, v):
        """Validate that at least one API key is provided."""
        if not v or not any(v.values()):
            raise ValueError("At least one API key must be provided")
        return v



class BatchTranslationRequest(BaseModel):
    """Request model for batch text translation."""
    texts: List[str] = Field(..., description="List of texts to translate", min_items=1, max_items=100)
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code") 
    context: Optional[str] = Field(None, description="Optional context for better translation")
    api_keys: Dict[str, str] = Field(..., description="Provider API keys")
    
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


class TranslationResponse(BaseModel):
    """Response model for translation results."""
    translated_text: str
    provider_used: str
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


class LanguagesResponse(BaseModel):
    """Response model for supported languages."""
    languages: Dict[str, Dict[str, Any]]
    providers: List[str]


class ProviderValidationResponse(BaseModel):
    """Response model for API key validation."""
    validation_results: Dict[str, bool]
    available_providers: List[str]



@router.post("/", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate a single text using cascading fallback providers.
    """
    try:
        result = await provider_router.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            api_keys=request.api_keys,
            context=request.context
        )
        
        return TranslationResponse(
            translated_text=result.translated_text,
            provider_used=result.provider_used,
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
async def translate_batch(request: BatchTranslationRequest):
    """
    Translate multiple texts using cascading fallback providers.
    """
    try:
        results = await provider_router.batch_translate(
            texts=request.texts,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            api_keys=request.api_keys,
            context=request.context
        )
        
        response_results = [
            TranslationResponse(
                translated_text=result.translated_text,
                provider_used=result.provider_used,
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
            successful_translations=len(results)
        )
        
    except TranslationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



@router.get("/languages", response_model=LanguagesResponse)
async def get_supported_languages():
    """
    Get supported language pairs and their directions.
    """
    try:
        supported_langs = provider_router.get_supported_languages()
        
        # Create language information with directions
        languages = {}
        for provider, langs in supported_langs.items():
            for lang in langs:
                if lang not in languages:
                    direction = provider_router.get_language_direction(lang)
                    languages[lang] = {
                        "code": lang,
                        "direction": direction.value,
                        "supported_by": []
                    }
                languages[lang]["supported_by"].append(provider)
        
        return LanguagesResponse(
            languages=languages,
            providers=list(supported_langs.keys())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/validate", response_model=ProviderValidationResponse)
async def validate_api_keys(api_keys: Dict[str, str]):
    """
    Validate API keys for translation providers.
    """
    try:
        validation_results = await provider_router.validate_api_keys(api_keys)
        available_providers = provider_router.get_available_providers(api_keys)
        
        return ProviderValidationResponse(
            validation_results=validation_results,
            available_providers=available_providers
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/providers")
async def get_providers():
    """
    Get list of available translation providers and their order.
    """
    try:
        return {
            "providers": [
                {"name": "openai", "order": 1, "description": "OpenAI GPT (Primary)"},
                {"name": "anthropic", "order": 2, "description": "Anthropic Claude (Secondary)"},
                {"name": "mistral", "order": 3, "description": "Mistral AI (Tertiary)"},
                {"name": "deepseek", "order": 4, "description": "DeepSeek (Fallback)"}
            ],
            "fallback_order": "Providers are tried in order until one succeeds"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
