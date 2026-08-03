"""Common normalized schema. Every ingest adapter must emit List[Conversation]."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional
import json


@dataclass
class Attachment:
    name: str
    kind: str = "unknown"      # image | file | code | ...
    ref: Optional[str] = None  # path/url/filename as found in the export (best-effort)


@dataclass
class Message:
    role: str                  # "user" | "assistant" | "system"
    content: str
    ts: Optional[str] = None
    attachments: List[Attachment] = field(default_factory=list)


@dataclass
class Conversation:
    source: str                # chatgpt | claude | gemini | generic | ...
    title: str
    messages: List[Message] = field(default_factory=list)
    id: Optional[str] = None

    def to_text(self, max_chars: Optional[int] = None) -> str:
        lines = [f"# {self.title}  (source: {self.source})", ""]
        for m in self.messages:
            who = {"user": "USER", "assistant": "ASSISTANT", "system": "SYSTEM"}.get(m.role, m.role.upper())
            lines.append(f"### {who}")
            lines.append(m.content.strip())
            if m.attachments:
                names = ", ".join(a.name for a in m.attachments)
                lines.append(f"[attachments: {names}]")
            lines.append("")
        text = "\n".join(lines)
        if max_chars and len(text) > max_chars:
            text = text[:max_chars] + "\n\n[...troncato...]"
        return text

    def to_dict(self) -> dict:
        return asdict(self)


def dump_json(convs: List[Conversation], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in convs], f, ensure_ascii=False, indent=2)
