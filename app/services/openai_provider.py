"""
OpenAI GPT provider for translation services.
"""
import asyncio
from typing import List, Optional
import openai
from openai import AsyncOpenAI
from .translation_provider import TranslationProvider, ProviderError


class OpenAIProvider(TranslationProvider):
    """OpenAI GPT translation provider."""
    
    def __init__(self):
        super().__init__("openai")
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
        """Translate text using OpenAI GPT."""
        try:
            client = AsyncOpenAI(api_key=api_key)
            prompt = self._create_openai_prompt(text, source_lang, target_lang, context)
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional translator. Provide only the translated text without explanations."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            translation = response.choices[0].message.content.strip()
            if not translation:
                raise ProviderError(self.name, "Empty translation response")
            return translation
            
        except openai.AuthenticationError as e:
            raise ProviderError(self.name, f"Authentication failed: {str(e)}", e)
        except openai.RateLimitError as e:
            raise ProviderError(self.name, f"Rate limit exceeded: {str(e)}", e)
        except openai.APIError as e:
            raise ProviderError(self.name, f"API error: {str(e)}", e)
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
        """Translate multiple texts using OpenAI GPT."""
        if not texts:
            return []
        
        # For batch operations, use concurrent translation
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
        """Validate OpenAI API key."""
        try:
            client = AsyncOpenAI(api_key=api_key)
            await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except openai.AuthenticationError:
            return False
        except Exception:
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Get supported language codes."""
        return self.supported_languages.copy()
    
    def _create_openai_prompt(self, text: str, source_lang: str, target_lang: str, context: Optional[str] = None) -> str:
        """Create optimized prompt for OpenAI."""
        return self.optimize_prompt_for_provider(text, source_lang, target_lang, context)
