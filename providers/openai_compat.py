import os
import requests


class OpenAICompatProvider:
    """Works for any /chat/completions endpoint: OpenAI, DeepSeek, Moonshot(Kimi),
    xAI(Grok), Perplexity."""

    def __init__(self, base_url: str, api_key_env: str, model: str, label: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.key = os.getenv(api_key_env)
        self.env = api_key_env
        self.label = label or base_url

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        if not self.key:
            raise RuntimeError(f"{self.env} not set (for {self.label})")
        r = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
