"""Honest stubs. These platforms expose no read-API for chat history;
extraction means scraping the page. For now, save the chat as .md and use
the `generic` adapter. Replace a stub with a real scraper/Takeout parser later.
"""


def make_stub(name: str, hint: str):
    def _load(path: str):
        raise NotImplementedError(
            f"[{name}] no direct extractor yet. {hint}\n"
            f"Workaround: copy the conversation into a .md file and run with --source generic."
        )
    return _load
