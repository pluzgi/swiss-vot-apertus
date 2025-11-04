"""
Swisscom Apertus API Client
Client for Swisscom's Apertus 70B language model
"""

import httpx
import logging
from typing import Dict, List, Optional, AsyncIterator
import json

from config import settings, get_apertus_api_key

logger = logging.getLogger(__name__)


class ApertusClient:
    """
    Client for Swisscom Apertus API (Swiss AI Platform)

    Rate Limits:
    - 5 requests per second (300/minute)
    - 100,000 tokens per minute

    Response headers provide rate limit status:
    - X-Ratelimit-Remaining-Tokens
    - X-Ratelimit-Reset-Tokens
    """

    def __init__(self, api_key: str = None, api_url: str = None):
        """
        Initialize Apertus client

        Args:
            api_key: Swiss AI Platform API key (default from settings)
            api_url: API base URL (default from settings)
        """
        self.api_key = api_key or get_apertus_api_key()
        self.api_url = api_url or settings.APERTUS_API_URL
        self.model = settings.APERTUS_MODEL

        if not self.api_key:
            logger.warning("⚠️  SWISS_AI_PLATFORM_API_KEY not set. API calls will fail.")
            logger.info("Set SWISS_AI_PLATFORM_API_KEY or APERTUS_API_KEY environment variable")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _log_rate_limits(self, response: httpx.Response):
        """Log rate limit information from response headers"""
        remaining = response.headers.get("X-Ratelimit-Remaining-Tokens")
        reset = response.headers.get("X-Ratelimit-Reset-Tokens")
        if remaining:
            logger.debug(f"Rate limit - Remaining tokens: {remaining}, Reset: {reset}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict:
        """
        Create a chat completion

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Returns:
            Response dict with choices, usage, etc.
        """
        endpoint = f"{self.api_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        logger.info(f"Apertus API call: {len(messages)} messages, stream={stream}")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    endpoint,
                    headers=self.headers,
                    json=payload
                )

                response.raise_for_status()
                self._log_rate_limits(response)

                if stream:
                    # Return streaming response handler
                    return response
                else:
                    result = response.json()
                    tokens = result.get('usage', {}).get('total_tokens', 0)
                    logger.info(f"✅ Apertus response received ({tokens} tokens)")
                    return result

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Apertus API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ Apertus API request failed: {e}")
            raise

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        """
        Stream chat completion chunks

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            SSE-formatted chunks
        """
        endpoint = f"{self.api_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        logger.info(f"Apertus streaming call: {len(messages)} messages")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    endpoint,
                    headers=self.headers,
                    json=payload
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            chunk = line[6:]  # Remove "data: " prefix

                            if chunk.strip() == "[DONE]":
                                logger.info("✅ Streaming completed")
                                break

                            try:
                                data = json.loads(chunk)
                                if "choices" in data and len(data["choices"]) > 0:
                                    content = data["choices"][0].get("delta", {}).get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Streaming error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"❌ Streaming failed: {e}")
            raise

    def format_messages(
        self,
        user_query: str,
        system_prompt: str = None,
        context: str = None
    ) -> List[Dict[str, str]]:
        """
        Format messages for Apertus API

        Args:
            user_query: User's question
            system_prompt: System prompt (optional)
            context: Retrieved context from RAG (optional)

        Returns:
            List of formatted message dicts
        """
        messages = []

        # System message
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # User message with optional context
        user_content = user_query
        if context:
            user_content = f"{context}\n\n---\n\nFrage: {user_query}"

        messages.append({
            "role": "user",
            "content": user_content
        })

        return messages

    async def test_connection(self) -> bool:
        """Test API connection with a simple request"""
        try:
            messages = [{"role": "user", "content": "Hello"}]
            result = await self.chat_completion(
                messages=messages,
                max_tokens=10
            )
            logger.info("✅ Apertus API connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Apertus API connection failed: {e}")
            return False


# Singleton instance
_apertus_client = None


def get_apertus_client() -> ApertusClient:
    """Get or create ApertusClient singleton"""
    global _apertus_client
    if _apertus_client is None:
        _apertus_client = ApertusClient()
    return _apertus_client
