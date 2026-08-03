"""Fallback loader: any chat you saved yourself as .md / .txt / .json.

- .json: list of {role|sender, content|text} OR our own dumped schema.
- .md/.txt: split on role headers. Recognizes lines like:
    "USER:", "ASSISTANT:", "### USER", "**User**", "You:", "Me:", "AI:"
  Anything before the first header becomes one user turn.
Use this for Perplexity / Grok / Gemini / DeepSeek / Kimi: copy the page
into a .md file and point the tool at it.
"""
from __future__ import annotations
import json
import os
import re
from typing import List
from schema import Conversation, Message

_USER = re.compile(r"^\s*(#+\s*)?(\*\*)?\s*(user|you|me|human)\s*(\*\*)?\s*[:>].*", re.I)
_ASST = re.compile(r"^\s*(#+\s*)?(\*\*)?\s*(assistant|ai|bot|gpt|claude|gemini|grok)\s*(\*\*)?\s*[:>].*", re.I)


def _from_json(data, path) -> List[Conversation]:
    if isinstance(data, list) and data and isinstance(data[0], dict) and "messages" in data[0]:
        # our own dumped schema
        convs = []
        for c in data:
            msgs = [Message(role=m["role"], content=m.get("content", "")) for m in c["messages"]]
            convs.append(Conversation(source=c.get("source", "generic"), title=c.get("title", "Untitled"), messages=msgs))
        return convs
    rows = data if isinstance(data, list) else data.get("messages", [])
    msgs = []
    for m in rows:
        role = m.get("role") or {"human": "user"}.get(m.get("sender"), m.get("sender")) or "user"
        role = "user" if role in ("human", "you", "me") else ("assistant" if role in ("ai", "bot") else role)
        msgs.append(Message(role=role, content=m.get("content") or m.get("text") or ""))
    title = os.path.splitext(os.path.basename(path))[0]
    return [Conversation(source="generic", title=title, messages=msgs)]


def _from_text(text: str, path: str) -> List[Conversation]:
    msgs: List[Message] = []
    cur_role, buf = None, []

    def flush():
        if buf and cur_role:
            msgs.append(Message(role=cur_role, content="\n".join(buf).strip()))

    for line in text.splitlines():
        if _USER.match(line):
            flush(); buf = []; cur_role = "user"
            buf.append(re.sub(r"^\s*(#+\s*)?(\*\*)?\s*\w+\s*(\*\*)?\s*[:>]\s*", "", line))
        elif _ASST.match(line):
            flush(); buf = []; cur_role = "assistant"
            buf.append(re.sub(r"^\s*(#+\s*)?(\*\*)?\s*\w+\s*(\*\*)?\s*[:>]\s*", "", line))
        else:
            if cur_role is None:
                cur_role = "user"
            buf.append(line)
    flush()
    title = os.path.splitext(os.path.basename(path))[0]
    return [Conversation(source="generic", title=title, messages=[m for m in msgs if m.content])]


def load(path: str) -> List[Conversation]:
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    if path.lower().endswith(".json"):
        return _from_json(json.loads(raw), path)
    return _from_text(raw, path)
