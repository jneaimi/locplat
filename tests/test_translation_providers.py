"""
Basic tests for the translation provider system.
"""
import pytest
from unittest.mock import AsyncMock
from app.services.openai_provider import OpenAIProvider
from app.services.provider_router import ProviderRouter


class TestTranslationProvider:
    """Test cases for translation providers."""
    
    def test_openai_provider_init(self):
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider()
        assert provider.get_provider_name() == "openai"
        assert "en" in provider.get_supported_languages()
        assert "ar" in provider.get_supported_languages()
        assert "bs" in provider.get_supported_languages()
    
    def test_provider_router_init(self):
        """Test provider router initialization."""
        router = ProviderRouter()
        assert len(router.providers) == 4
        assert router.provider_names == ["openai", "anthropic", "mistral", "deepseek"]
    
    def test_language_direction_detection(self):
        """Test language direction detection."""
        provider = OpenAIProvider()
        
        # Test RTL languages
        assert provider.get_language_direction("ar").value == "rtl"
        assert provider.get_language_direction("he").value == "rtl"
        
        # Test LTR languages
        assert provider.get_language_direction("en").value == "ltr"
        assert provider.get_language_direction("bs").value == "ltr"
        assert provider.get_language_direction("fr").value == "ltr"
    
    def test_language_pair_support(self):
        """Test language pair support checking."""
        provider = OpenAIProvider()
        
        assert provider.supports_language_pair("en", "ar") is True
        assert provider.supports_language_pair("en", "bs") is True
        assert provider.supports_language_pair("xx", "yy") is False
    
    @pytest.mark.asyncio
    async def test_translation_quality_assessment(self):
        """Test translation quality assessment."""
        provider = OpenAIProvider()
        
        # Test good translation
        quality = await provider.assess_translation_quality(
            "Hello world", "مرحبا بالعالم", "en", "ar"
        )
        assert 0.0 <= quality <= 1.0
        
        # Test empty translation
        quality = await provider.assess_translation_quality(
            "Hello world", "", "en", "ar"
        )
        assert quality == 0.0
        
        # Test identical text (likely untranslated)
        quality = await provider.assess_translation_quality(
            "Hello world", "Hello world", "en", "ar"
        )
        assert quality == 0.2
    
    def test_prompt_optimization(self):
        """Test prompt optimization for different languages."""
        provider = OpenAIProvider()
        
        # Test Arabic prompt (should include cultural sensitivity)
        prompt = provider.optimize_prompt_for_provider("Hello", "en", "ar")
        assert "cultural sensitivity" in prompt
        assert "formal register" in prompt
        
        # Test Bosnian prompt (should specify Latin script)
        prompt = provider.optimize_prompt_for_provider("Hello", "en", "bs")
        assert "Latin script" in prompt
        
        # Test with context
        prompt = provider.optimize_prompt_for_provider("Hello", "en", "ar", "greeting")
        assert "Context: greeting" in prompt


class TestProviderRouter:
    """Test cases for provider router."""
    
    def test_router_initialization(self):
        """Test router initialization."""
        router = ProviderRouter()
        assert len(router.providers) == 4
        available = router.get_available_providers({"openai": "test-key"})
        assert available == ["openai"]
    
    def test_get_supported_languages(self):
        """Test getting supported languages from all providers."""
        router = ProviderRouter()
        languages = router.get_supported_languages()
        
        assert "openai" in languages
        assert "anthropic" in languages
        assert "mistral" in languages
        assert "deepseek" in languages
        
        for provider_langs in languages.values():
            assert "en" in provider_langs
            assert "ar" in provider_langs
            assert "bs" in provider_langs
    
    @pytest.mark.asyncio
    async def test_api_key_validation_empty_keys(self):
        """Test API key validation with empty keys."""
        router = ProviderRouter()
        
        # Mock all providers to avoid actual API calls
        for provider in router.providers:
            provider.validate_api_key = AsyncMock(return_value=False)
        
        results = await router.validate_api_keys({})
        
        for provider_name in router.provider_names:
            assert results[provider_name] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
