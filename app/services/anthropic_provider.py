"""
Anthropic Claude provider for translation services.
"""
import asyncio
from typing import List, Optional
import anthropic
from anthropic import AsyncAnthropic
from .translation_provider import TranslationProvider, ProviderError


class AnthropicProvider(TranslationProvider):
    """Anthropic Claude translation provider."""
    
    def __init__(self):
        super().__init__("anthropic")
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
        """Translate text using Anthropic Claude."""
        try:
            client = AsyncAnthropic(api_key=api_key)
            prompt = self._create_anthropic_prompt(text, source_lang, target_lang, context)
            
            response = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.3,
                system="You are a professional translator. Translate the given text accurately and provide ONLY the translated text. Do not add any notes, explanations, disclaimers, or additional commentary. Return only the direct translation.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            translation = response.content[0].text.strip()
            if not translation:
                raise ProviderError(self.name, "Empty translation response")
            return translation
            
        except anthropic.AuthenticationError as e:
            raise ProviderError(self.name, f"Authentication failed: {str(e)}", e)
        except anthropic.RateLimitError as e:
            raise ProviderError(self.name, f"Rate limit exceeded: {str(e)}", e)
        except anthropic.APIError as e:
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
        """Translate multiple texts using Anthropic Claude."""
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
        """Validate Anthropic API key."""
        try:
            client = AsyncAnthropic(api_key=api_key)
            await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except anthropic.AuthenticationError:
            return False
        except Exception:
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Get supported language codes."""
        return self.supported_languages.copy()
    
    def _create_anthropic_prompt(self, text: str, source_lang: str, target_lang: str, context: Optional[str] = None) -> str:
        """Create optimized prompt for Anthropic Claude."""
        base_prompt = self.optimize_prompt_for_provider(text, source_lang, target_lang, context)
        # Claude-specific enhancement
        return f"You are a professional translator. {base_prompt}\n\nProvide only the translation, no explanations."
