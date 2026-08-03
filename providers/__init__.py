"""Target-model providers for the opinion. Each: complete(system, user) -> str.

Auth via env vars. Model IDs are env-overridable because vendor model
strings change often — do not trust the defaults blindly, set them yourself
with --model or via env.
"""
import os
from .anthropic_p import AnthropicProvider
from .openai_compat import OpenAICompatProvider
from .gemini_p import GeminiProvider

# name -> (base_url, api_key_env, default_model, verified?)
_OPENAI_COMPAT = {
    "openai":     ("https://api.openai.com/v1",                          "OPENAI_API_KEY",     "gpt-5.1",             True),
    "deepseek":   ("https://api.deepseek.com",                           "DEEPSEEK_API_KEY",   "deepseek-chat",      True),
    "kimi":       ("https://api.moonshot.ai/v1",                         "MOONSHOT_API_KEY",   "kimi-k2",            True),
    "grok":       ("https://api.x.ai/v1",                                "XAI_API_KEY",        "grok-4",             True),
    "perplexity": ("https://api.perplexity.ai",                          "PERPLEXITY_API_KEY", "sonar-pro",          True),
    # --- Chinese models (OpenAI-compatible) ---
    "qwen":       ("https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "DASHSCOPE_API_KEY", "qwen-plus",       True),
    "glm":        ("https://open.bigmodel.cn/api/paas/v4",               "ZHIPU_API_KEY",      "glm-4.6",           True),
    "minimax":    ("https://api.minimax.io/v1",                          "MINIMAX_API_KEY",    "MiniMax-Text-01",   False),  # VERIFY base url
    # --- Aggregator: one key, most models incl. all Chinese ones ---
    "openrouter": ("https://openrouter.ai/api/v1",                       "OPENROUTER_API_KEY", "deepseek/deepseek-chat", True),
}


def get_provider(name: str, model: str | None = None):
    if name == "anthropic":
        return AnthropicProvider(model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5"))
    if name == "gemini":
        return GeminiProvider(model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    if name in _OPENAI_COMPAT:
        base, env, default_model, verified = _OPENAI_COMPAT[name]
        if not verified:
            print(f"  [!] '{name}': base URL not verified — if it fails, fix it in providers/__init__.py")
        return OpenAICompatProvider(base_url=base, api_key_env=env, model=model or default_model, label=name)
    raise ValueError(f"Unknown provider '{name}'. Known: anthropic, gemini, {', '.join(_OPENAI_COMPAT)}")
