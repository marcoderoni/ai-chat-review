import os
import requests


class GeminiProvider:
    def __init__(self, model: str):
        self.model = model
        self.key = os.getenv("GEMINI_API_KEY")

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        if not self.key:
            raise RuntimeError("GEMINI_API_KEY not set")
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent?key={self.key}")
        r = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            },
            timeout=120,
        )
        r.raise_for_status()
        cands = r.json().get("candidates", [])
        if not cands:
            return ""
        return "".join(p.get("text", "") for p in cands[0]["content"]["parts"])
