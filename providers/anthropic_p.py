import os
import requests


class AnthropicProvider:
    def __init__(self, model: str):
        self.model = model
        self.key = os.getenv("ANTHROPIC_API_KEY")

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        if not self.key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=120,
        )
        r.raise_for_status()
        blocks = r.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
