"""Parse ChatGPT data export (conversations.json).

The export stores each conversation as a `mapping` graph of nodes
(id -> {message, parent, children}). We walk from the current leaf up to
the root to reconstruct the active linear thread.
"""
from __future__ import annotations
import json
from typing import List
from schema import Conversation, Message, Attachment


def _node_text(msg: dict) -> str:
    if not msg:
        return ""
    content = msg.get("content") or {}
    ctype = content.get("content_type")
    if ctype == "text":
        return "\n".join(content.get("parts") or [])
    if ctype == "code":
        return "```\n" + (content.get("text") or "") + "\n```"
    if ctype in ("multimodal_text",):
        out = []
        for p in content.get("parts") or []:
            if isinstance(p, str):
                out.append(p)
            elif isinstance(p, dict):
                out.append(f"[{p.get('content_type', 'part')}]")
        return "\n".join(out)
    parts = content.get("parts")
    if parts:
        return "\n".join(x for x in parts if isinstance(x, str))
    return ""


def _attachments(msg: dict) -> List[Attachment]:
    out = []
    meta = (msg or {}).get("metadata") or {}
    for a in meta.get("attachments") or []:
        out.append(Attachment(name=a.get("name", "file"), kind=a.get("mime_type", "file"), ref=a.get("id")))
    return out


def _linearize(mapping: dict, current: str | None) -> List[dict]:
    # follow current_node up to root, then reverse
    chain, node_id = [], current
    if not node_id:  # fallback: pick any leaf
        node_id = next((nid for nid, n in mapping.items() if not n.get("children")), None)
    while node_id and node_id in mapping:
        chain.append(mapping[node_id])
        node_id = mapping[node_id].get("parent")
    return list(reversed(chain))


def load(path: str) -> List[Conversation]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):  # some exports wrap it
        data = data.get("conversations", [data])

    convs: List[Conversation] = []
    for conv in data:
        mapping = conv.get("mapping") or {}
        nodes = _linearize(mapping, conv.get("current_node"))
        msgs: List[Message] = []
        for node in nodes:
            msg = node.get("message")
            if not msg:
                continue
            role = (msg.get("author") or {}).get("role")
            if role not in ("user", "assistant", "system"):
                continue
            text = _node_text(msg).strip()
            atts = _attachments(msg)
            if not text and not atts:
                continue
            ts = msg.get("create_time")
            msgs.append(Message(role=role, content=text, ts=str(ts) if ts else None, attachments=atts))
        if not msgs:
            continue
        convs.append(Conversation(
            source="chatgpt",
            title=conv.get("title") or "Untitled",
            id=conv.get("conversation_id") or conv.get("id"),
            messages=msgs,
        ))
    return convs
