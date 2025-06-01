"""
Mistral AI provider for translation services.
"""
import asyncio
from typing import List, Optional
import httpx
from .translation_provider import TranslationProvider, ProviderError


class MistralProvider(TranslationProvider):
    """Mistral AI translation provider."""
    
    def __init__(self):
        super().__init__("mistral")
        self.api_base = "https://api.mistral.ai/v1"
        self.supported_languages = [
            'en', 'ar', 'bs', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 
            'ja', 'ko', 'hi', 'tr', 'pl', 'nl', 'sv', 'da', 'no', 'fi'
        ]
        
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str, 
        api_key: str,
        context: Optional[str] = None
    ) -> str:
        """Translate text using Mistral AI."""
        try:
            async with httpx.AsyncClient() as client:
                prompt = self._create_mistral_prompt(text, source_lang, target_lang, context)
                
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistral-small",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a professional translator. Provide only the translated text without explanations."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    },
                    timeout=30.0
                )
                
                if response.status_code == 401:
                    raise ProviderError(self.name, "Authentication failed - invalid API key")
                elif response.status_code == 429:
                    raise ProviderError(self.name, "Rate limit exceeded")
                elif response.status_code != 200:
                    raise ProviderError(self.name, f"API error: {response.status_code}")
                
                data = response.json()
                translation = data["choices"][0]["message"]["content"].strip()
                
                if not translation:
                    raise ProviderError(self.name, "Empty translation response")
                    
                return translation
                
        except httpx.HTTPError as e:
            raise ProviderError(self.name, f"HTTP error: {str(e)}", e)
        except Exception as e:
            raise ProviderError(self.name, f"Unexpected error: {str(e)}", e)
    
    async def batch_translate(
        self, 
        texts: List[str], 
        source_lang: str, 
        target_lang: str, 
        api_key: str,
        context: Optional[str] = None
    ) -> List[str]:
        """Translate multiple texts using Mistral AI."""
        if not texts:
            return []
        
        tasks = [
            self.translate(text, source_lang, target_lang, api_key, context)
            for text in texts
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            translations = []
            for result in results:
                if isinstance(result, Exception):
                    raise result
                translations.append(result)
            return translations
        except Exception as e:
            raise ProviderError(self.name, f"Batch translation failed: {str(e)}", e)
    
    async def validate_api_key(self, api_key: str) -> bool:
        """Validate Mistral API key."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistral-small",
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 1
                    },
                    timeout=10.0
                )
                return response.status_code != 401
        except Exception:
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Get supported language codes."""
        return self.supported_languages.copy()
    
    def _create_mistral_prompt(self, text: str, source_lang: str, target_lang: str, context: Optional[str] = None) -> str:
        """Create optimized prompt for Mistral AI."""
        return self.optimize_prompt_for_provider(text, source_lang, target_lang, context)
