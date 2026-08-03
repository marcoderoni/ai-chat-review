"""Extract plain text from attachment files so it can be inlined into the review.

Text (not base64): cheap on tokens and works with every provider, not just
multimodal ones. Supported: .pdf .txt .md .csv .json .docx
"""
import os


def extract_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _pdf(path)
    if ext in (".txt", ".md", ".csv", ".json", ".log"):
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    if ext == ".docx":
        return _docx(path)
    raise ValueError(f"unsupported type '{ext}' (supported: pdf, txt, md, csv, json, docx)")


def _pdf(path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("pypdf not installed — run: pip3 install pypdf")
    reader = PdfReader(path)
    pages = [(p.extract_text() or "").strip() for p in reader.pages]
    text = "\n\n".join(p for p in pages if p)
    if not text.strip():
        raise RuntimeError("no extractable text (scanned/image PDF? OCR needed, not supported in v1)")
    return text


def _docx(path: str) -> str:
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError("python-docx not installed — run: pip3 install python-docx")
    d = Document(path)
    return "\n".join(p.text for p in d.paragraphs if p.text)


def build_block(paths) -> str:
    """Turn a list of file paths into a text block to append to the prompt.
    Failures are reported and skipped, never fatal."""
    if not paths:
        return ""
    chunks = []
    for p in paths:
        name = os.path.basename(p)
        try:
            txt = extract_text(p)
            chunks.append(f"\n\n--- ATTACHED FILE: {name} ---\n{txt}")
            print(f"[attach] {name}: {len(txt)} chars")
        except Exception as e:
            print(f"[attach] SKIP {name}: {e}")
    return "".join(chunks)
