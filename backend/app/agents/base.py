from abc import ABC, abstractmethod
from dataclasses import dataclass

import openai
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.security.api_key_vault import get_nim_api_key


class BaseAgent(ABC):
    model: str = ""
    system_prompt: str = ""
    temperature: float = 0.2
    timeout: int = 60

    def __init__(self) -> None:
        self.client = openai.AsyncOpenAI(
            base_url=settings.NIM_BASE_URL,
            api_key=get_nim_api_key(),
            timeout=self.timeout,
            max_retries=0,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(openai.APIConnectionError),
        reraise=True,
    )
    async def _call_nim(self, messages: list[dict]) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("Empty response from NIM")
            return content
        except openai.APIStatusError as exc:
            if exc.status_code < 500:
                raise
            raise RuntimeError(f"NIM 5xx: {exc}") from exc
        except openai.APIConnectionError as exc:
            raise

    @abstractmethod
    async def run(self, context: dict) -> dataclass:
        raise NotImplementedError
