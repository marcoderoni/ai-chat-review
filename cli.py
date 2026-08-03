#!/usr/bin/env python3
"""ai-chat-review — extract a chat from one AI system and ask another model for its opinion.

Examples:
  python3 cli.py list   --source claude  --input conversations.json
  python3 cli.py review --source chatgpt --input conversations.json --which 3    --provider anthropic
  python3 cli.py review --source claude  --input conversations.json --which all  --provider openrouter
  python3 cli.py review --source claude  --input conversations.json --which all  --provider qwen --resume
  python3 cli.py review --source generic --input mychat.md --provider grok --prompt-file my_prompt.txt
"""
import argparse
import csv
import json
import os
import re
import sys
import time

from ingest import get_adapter
from providers import get_provider
from review import review as run_review
from attachments import build_block
from schema import dump_json

MANIFEST_CSV = "_manifest.csv"
MANIFEST_JSON = "_manifest.json"
_FIELDS = ["index", "title", "source", "provider", "status", "output_file", "error", "ts"]


def _select(convs, which):
    if which in (None, "all"):
        return list(enumerate(convs))
    if ":" in which:
        a, b = which.split(":")
        return list(enumerate(convs))[(int(a) if a else 0):(int(b) if b else len(convs))]
    i = int(which)
    return [(i, convs[i])]


def _slug(s):
    return re.sub(r"[^\w\-]+", "_", s).strip("_")[:60] or "chat"


def _load_manifest(out):
    path = os.path.join(out, MANIFEST_JSON)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return {row["index"]: row for row in json.load(f)}
    return {}


def _save_manifest(out, rows):
    data = list(rows.values())
    with open(os.path.join(out, MANIFEST_JSON), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out, MANIFEST_CSV), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=_FIELDS)
        w.writeheader()
        w.writerows(data)


def _resolve_prompt(args):
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as f:
            return f.read().strip()
    if args.prompt:
        return args.prompt
    # no prompt supplied: ask (if interactive), otherwise use the default
    if sys.stdin.isatty():
        print("Custom review prompt? (press enter to use the default)")
        txt = input("> ").strip()
        if txt:
            return txt
    return None  # -> review.py uses DEFAULT_SYSTEM


def cmd_list(args):
    convs = get_adapter(args.source)(args.input)
    for i, c in enumerate(convs):
        print(f"[{i}] {c.title}  ({len(c.messages)} msg)")
    print(f"\n{len(convs)} conversations.")


def cmd_review(args):
    convs = get_adapter(args.source)(args.input)
    provider = get_provider(args.provider, args.model)
    os.makedirs(args.out, exist_ok=True)
    system_override = _resolve_prompt(args)
    attach_block = build_block(args.attach)

    manifest = _load_manifest(args.out) if args.resume else {}
    selected = _select(convs, args.which)
    done_count = fail_count = skip_count = 0

    for i, c in selected:
        key = str(i)
        if args.resume and manifest.get(key, {}).get("status") == "done":
            skip_count += 1
            print(f"~ [{i}] {c.title} — already done, skipping")
            continue
        print(f"-> [{i}] {c.title} ... ", end="", flush=True)
        row = {"index": key, "title": c.title, "source": c.source,
               "provider": args.provider, "status": "", "output_file": "", "error": "",
               "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
        try:
            opinion = run_review(c, provider, lang=args.lang, system_override=system_override, extra_context=attach_block)
            fn = os.path.join(args.out, f"{i:03d}_{_slug(c.title)}__review_{args.provider}.md")
            with open(fn, "w", encoding="utf-8") as f:
                f.write(f"# Review by {args.provider} of \"{c.title}\"\n\n{opinion}\n")
            row["status"], row["output_file"] = "done", fn
            done_count += 1
            print(f"ok -> {fn}")
        except Exception as e:
            row["status"], row["error"] = "failed", str(e)[:300]
            fail_count += 1
            print(f"ERROR: {str(e)[:120]}")
        manifest[key] = row
        _save_manifest(args.out, manifest)  # save after EACH chat: crash-safe

    print(f"\nDone: {done_count} | Failed: {fail_count} | Skipped: {skip_count} "
          f"| Selected: {len(selected)}")
    print(f"Manifest: {os.path.join(args.out, MANIFEST_CSV)}  (resume with --resume)")


def cmd_normalize(args):
    convs = get_adapter(args.source)(args.input)
    dump_json(convs, args.out)
    print(f"{len(convs)} conversations -> {args.out}")


def main():
    p = argparse.ArgumentParser(description="Extract AI chats and ask another model for its opinion.")
    sub = p.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--source", required=True,
                        help="chatgpt|claude|generic|gemini|perplexity|grok|deepseek|kimi")
    common.add_argument("--input", required=True, help="export file or .md/.txt/.json")

    pl = sub.add_parser("list", parents=[common], help="list the conversations")
    pl.set_defaults(func=cmd_list)

    pn = sub.add_parser("normalize", parents=[common], help="export to the common JSON schema")
    pn.add_argument("--out", default="normalized.json")
    pn.set_defaults(func=cmd_normalize)

    pr = sub.add_parser("review", parents=[common], help="ask a target model for its opinion")
    pr.add_argument("--provider", required=True,
                    help="anthropic|openai|gemini|deepseek|kimi|grok|perplexity|qwen|glm|minimax|openrouter")
    pr.add_argument("--model", default=None, help="override the model id")
    pr.add_argument("--which", default="all", help="all | index (e.g. 3) | range (e.g. 0:10)")
    pr.add_argument("--lang", default="en", help="language of the opinion (en|it|nl|fr)")
    pr.add_argument("--prompt", default=None, help="custom review prompt, inline")
    pr.add_argument("--prompt-file", default=None, help="file containing the custom review prompt")
    pr.add_argument("--attach", action="append",
                    help="attach a file (pdf/txt/md/csv/json/docx); extracted as text. Repeatable.")
    pr.add_argument("--resume", action="store_true", help="skip chats already 'done' in the manifest")
    pr.add_argument("--out", default="reviews")
    pr.set_defaults(func=cmd_review)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, NotImplementedError, RuntimeError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
