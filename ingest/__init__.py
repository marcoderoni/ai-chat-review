"""Ingest registry. Each adapter: load(path) -> List[Conversation]."""
from .chatgpt import load as load_chatgpt
from .claude import load as load_claude
from .generic import load as load_generic
from .stubs import make_stub

ADAPTERS = {
    "chatgpt": load_chatgpt,     # ChatGPT Settings > Data export (conversations.json)
    "claude": load_claude,       # Claude Settings > Export data (conversations.json)
    "generic": load_generic,     # any .md/.txt/.json chat you paste/save yourself
    # No public read-API for these consumer histories -> scraping needed. Use `generic` for now:
    "gemini": make_stub("gemini", "Use Google Takeout export, then load as generic, or add a Takeout parser."),
    "perplexity": make_stub("perplexity", "No export/API; scrape the page to MD, then use generic."),
    "grok": make_stub("grok", "No export/API; scrape the page to MD, then use generic."),
    "deepseek": make_stub("deepseek", "Web export/scrape to MD, then use generic."),
    "kimi": make_stub("kimi", "Web export/scrape to MD, then use generic."),
}


def get_adapter(source: str):
    if source not in ADAPTERS:
        raise ValueError(f"Unknown source '{source}'. Known: {', '.join(ADAPTERS)}")
    return ADAPTERS[source]
