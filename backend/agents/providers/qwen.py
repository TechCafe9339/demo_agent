import requests

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

        self.timeout = settings.QWEN_TIMEOUT

    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> LLMResponse:

        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": temperature,
            },
        }

        if json_mode:
            payload["format"] = "json"

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.ConnectionError as exc:
            raise LLMConnectionError(
                "Unable to connect to Qwen/Ollama. " "Make sure Ollama is running."
            ) from exc

        except requests.Timeout as exc:
            raise LLMGenerationError("Qwen generation timed out.") from exc

        except requests.RequestException as exc:
            raise LLMGenerationError(f"Qwen request failed: {exc}") from exc

        data = response.json()

        message = data.get("message", {})

        content = message.get(
            "content",
            "",
        )

        return LLMResponse(
            content=content,
            model=data.get(
                "model",
                self.model,
            ),
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
            raw_response=data,
        )
