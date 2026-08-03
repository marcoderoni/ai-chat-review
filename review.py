"""Turn a conversation into a review request and collect the target model's answer."""
from __future__ import annotations
from schema import Conversation

_LANG = {"it": "Italian", "en": "English", "nl": "Dutch", "fr": "French"}

# Default review instruction, used when the user gives no custom prompt.
DEFAULT_SYSTEM = (
    "Please read the conversation below carefully and act as a genuine expert in the subject "
    "it covers. Do NOT continue the conversation: give me your OPINION on it. "
    "Answer in {lang} and structure it as:\n"
    "1. Overall, what do you think.\n"
    "2. Do you agree? Which points you agree with, which not, and why.\n"
    "3. What you would change, add, or remove.\n"
    "4. Errors, inaccuracies, or risks you notice.\n"
    "5. One-line verdict.\n"
    "Be direct and concrete, no filler."
)

USER_TMPL = (
    "Here is the conversation to evaluate (title: \"{title}\", source platform: {source}).\n"
    "--- BEGIN CONVERSATION ---\n{body}\n--- END CONVERSATION ---\n\n"
    "Give me your opinion."
)


def build_prompt(conv: Conversation, lang: str = "en", system_override: str | None = None,
                 extra_context: str = "", max_chars=None):
    system = system_override if system_override else DEFAULT_SYSTEM.format(lang=_LANG.get(lang, "English"))
    user = USER_TMPL.format(title=conv.title, source=conv.source, body=conv.to_text(max_chars=max_chars))
    if extra_context:
        user += extra_context
    return system, user


def review(conv: Conversation, provider, lang: str = "en", system_override: str | None = None,
           extra_context: str = "") -> str:
    system, user = build_prompt(conv, lang=lang, system_override=system_override, extra_context=extra_context)
    return provider.complete(system, user)
