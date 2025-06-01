"""
OpenAI GPT provider for translation services.
"""
from typing import List, Optional
import openai
from openai import AsyncOpenAI
from .translation_provider import BaseAsyncProvider, ProviderError


class OpenAIProvider(BaseAsyncProvider):
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
                        "content": "You are a professional translator. Translate the given text accurately and provide ONLY the translated text. Do not add any notes, explanations, disclaimers, or additional commentary. Return only the direct translation."
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
            raise ProviderError(self.name, f"Unexpected error: {str(e)}", e) from e
    
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
        except (openai.APIError, openai.RateLimitError, openai.APIConnectionError):
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Get supported language codes."""
        return self.supported_languages.copy()
    
    def _create_openai_prompt(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str, 
        context: Optional[str] = None
    ) -> str:
        """Create optimized prompt for OpenAI."""
        return self.optimize_prompt_for_provider(text, source_lang, target_lang, context)
