"""
Mistral AI provider for translation services.
"""
from typing import List, Optional
import httpx
from .translation_provider import BaseAsyncProvider, ProviderError


class MistralProvider(BaseAsyncProvider):
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

                # Clean up Mistral's tendency to add notes and disclaimers
                translation = self._clean_mistral_response(translation)

                if not translation:
                    raise ProviderError(self.name, "Empty translation response")

                return translation

        except httpx.HTTPError as e:
            raise ProviderError(self.name, f"HTTP error: {str(e)}", e)
        except Exception as e:
            raise ProviderError(self.name, f"Unexpected error: {str(e)}", e) from e

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
        except (httpx.HTTPError, httpx.ConnectError, httpx.RequestError):
            return False

    def get_supported_languages(self) -> List[str]:
        """Get supported language codes."""
        return self.supported_languages.copy()

    def _clean_mistral_response(self, translation: str) -> str:
        """
        Clean up Mistral's response by removing notes, disclaimers, and explanations.

        Args:
            translation: Raw translation response from Mistral

        Returns:
            Cleaned translation text only
        """
        import re

        # Remove common disclaimer patterns
        patterns_to_remove = [
            r'\n\n\(Note:.*?\)',  # Remove (Note: ...) at the end
            r'\n\nNote:.*',       # Remove Note: ... at the end
            r'\n\nDisclaimer:.*', # Remove Disclaimer: ... at the end
            r'\n\n\*.*?\*',       # Remove *italicized notes*
            r'\n\nThis translation.*', # Remove "This translation..." notes
            r'\n\nPlease note.*',      # Remove "Please note..." disclaimers
            r'\n\nFor.*context.*',     # Remove context-related notes
        ]

        cleaned = translation
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Remove any remaining double newlines and extra whitespace
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = cleaned.strip()

        return cleaned

    def _create_mistral_prompt(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str, 
        context: Optional[str] = None
    ) -> str:
        """Create optimized prompt for Mistral AI."""
        base_prompt = self.optimize_prompt_for_provider(text, source_lang, target_lang, context)

        # Add Mistral-specific instructions to avoid notes and disclaimers
        enhanced_prompt = (
            f"{base_prompt}\n\n"
            f"IMPORTANT: Provide ONLY the direct translation. "
            f"Do not add any notes, explanations, or disclaimers."
        )

        return enhanced_prompt
