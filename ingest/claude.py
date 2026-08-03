"""Parse Claude (claude.ai) data export (conversations.json).

Shape: list of conversations, each with `chat_messages`, where each message
has `sender` ("human"/"assistant"), `text` (and/or `content` blocks),
plus `attachments` and `files`.
"""
from __future__ import annotations
import json
from typing import List
from schema import Conversation, Message, Attachment

_ROLE = {"human": "user", "assistant": "assistant"}


def _text(m: dict) -> str:
    if m.get("text"):
        return m["text"]
    # newer exports use content blocks
    parts = []
    for blk in m.get("content") or []:
        if blk.get("type") == "text" and blk.get("text"):
            parts.append(blk["text"])
    return "\n".join(parts)


def _attachments(m: dict) -> List[Attachment]:
    out = []
    for a in m.get("attachments") or []:
        out.append(Attachment(name=a.get("file_name", "file"), kind="file", ref=a.get("id")))
    for fobj in m.get("files") or []:
        out.append(Attachment(name=fobj.get("file_name", "file"), kind="file"))
    return out


def load(path: str) -> List[Conversation]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("conversations", [data])

    convs: List[Conversation] = []
    for conv in data:
        msgs: List[Message] = []
        for m in conv.get("chat_messages") or conv.get("messages") or []:
            role = _ROLE.get(m.get("sender") or m.get("role"), None)
            if role is None:
                continue
            text = _text(m).strip()
            atts = _attachments(m)
            if not text and not atts:
                continue
            msgs.append(Message(role=role, content=text, ts=m.get("created_at"), attachments=atts))
        if not msgs:
            continue
        convs.append(Conversation(
            source="claude",
            title=conv.get("name") or conv.get("title") or "Untitled",
            id=conv.get("uuid") or conv.get("id"),
            messages=msgs,
        ))
    return convs
