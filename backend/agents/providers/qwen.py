import requests, os

from django.conf import settings

from .base import (
    LLMProvider,
    LLMResponse,
)

from .exceptions import (
    LLMConnectionError,
    LLMGenerationError,
)


class QwenProvider(LLMProvider):

    def __init__(self):
        self.base_url = settings.QWEN_BASE_URL.rstrip("/")

        self.model = settings.QWEN_MODEL

        self.timeout = int(
            os.getenv(
                "QWEN_TIMEOUT",
                "600",
            )
        )

    def generate(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.1,
        json_mode: bool = False,
        json_schema: dict | None = None,
    ) -> LLMResponse:

        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if json_schema is not None:
            payload["format"] = json_schema

        elif json_mode:
            payload["format"] = "json"

        response = requests.post(
            url,
            json=payload,
            timeout=(
                10,
                self.timeout,
            ),
        )

        response.raise_for_status()

        data = response.json()

        content = data.get("message", {}).get("content", "")

        return LLMResponse(content=content)
