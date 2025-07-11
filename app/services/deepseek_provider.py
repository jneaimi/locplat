"""
DeepSeek provider for translation services.
"""
from typing import List, Optional
import httpx
from .translation_provider import BaseAsyncProvider, ProviderError


class DeepSeekProvider(BaseAsyncProvider):
    """DeepSeek translation provider using OpenAI-compatible API."""

    def __init__(self):
        super().__init__("deepseek")
        self.api_base = "https://api.deepseek.com/v1"
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
        """Translate text using DeepSeek."""
        try:
            async with httpx.AsyncClient() as client:
                prompt = self._create_deepseek_prompt(text, source_lang, target_lang, context)

                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a professional translator. Translate the given text accurately and provide ONLY the translated text. Do not add any notes, explanations, disclaimers, or additional commentary. Return only the direct translation."
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
            raise ProviderError(self.name, f"Unexpected error: {str(e)}", e) from e

    async def validate_api_key(self, api_key: str) -> bool:
        """Validate DeepSeek API key."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": "test"}], "max_tokens": 1},
                    timeout=10.0
                )
                return response.status_code != 401
        except (httpx.HTTPError, httpx.ConnectError, httpx.RequestError):
            return False

    def get_supported_languages(self) -> List[str]:
        """Get supported language codes."""
        return self.supported_languages.copy()

    def _create_deepseek_prompt(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str, 
        context: Optional[str] = None
    ) -> str:
        """Create optimized prompt for DeepSeek."""
        return self.optimize_prompt_for_provider(text, source_lang, target_lang, context)
