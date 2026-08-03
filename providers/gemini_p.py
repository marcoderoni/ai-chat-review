import os
import requests


class GeminiProvider:
    def __init__(self, model: str):
        self.model = model
        self.key = os.getenv("GEMINI_API_KEY")

    def complete(self, system: str, user: str, max_tokens: int = 4000) -> str:
        if not self.key:
            raise RuntimeError("GEMINI_API_KEY not set")
        url = (f"https://generativelanguage.googleapis.com/v1/models/"
               f"{self.model}:generateContent?key={self.key}")
        prompt = f"{system}\n\n{user}" if system else user
        r = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            },
            timeout=120,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"{r.status_code}: {r.text[:400]}")
        cands = r.json().get("candidates", [])
        if not cands:
            return ""
        parts = cands[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)
