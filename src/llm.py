"""LLM client. Local mode does not call a network. OpenAI mode uses env vars."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from src.config import LLM_PROVIDER, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


class LLMClient:
    def __init__(self, provider: str | None = None) -> None:
        chosen = (provider or LLM_PROVIDER or "local").lower()
        if chosen == "auto":
            chosen = "openai" if OPENAI_API_KEY else "local"
        if chosen == "openai" and not OPENAI_API_KEY:
            raise RuntimeError(
                "LLM_PROVIDER=openai but OPENAI_API_KEY is empty. "
                "Set the key in the environment or .env, or use LLM_PROVIDER=local."
            )
        self.provider = chosen
        self.model = OPENAI_MODEL

    @property
    def uses_api(self) -> bool:
        return self.provider == "openai"

    def complete(self, system: str, user: str) -> str:
        if not self.uses_api:
            raise RuntimeError("Local provider has no free-form completion.")
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        request = urllib.request.Request(
            f"{OPENAI_BASE_URL}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM request failed ({error.code}): {detail}") from error
        return body["choices"][0]["message"]["content"].strip()
