# ai-chat-review

Extract a chat from one AI system and ask **another model for its opinion** on it:
does it agree? would it say something different, more, or less?

## What it does (and does NOT)

- ✅ Reads ChatGPT and Claude **exports**, or any chat you saved as `.md/.txt/.json` (`generic` loader).
- ✅ Sends the chat (1 / N / all) to a target model via its **completion API** and saves the opinion as Markdown.
- ❌ Does **not** recreate the conversation as a native thread inside the other app: developer APIs are *stateless* and separate from your consumer chat data. The only vendor with native chat-history import is Gemini (from its own UI, not from here).
- ⚠️ Perplexity / Grok / Gemini / DeepSeek / Kimi have **no API to read your history**: export them (Takeout) or copy them into a `.md` file and load with `--source generic`. The stubs say so explicitly.

## How extraction works, per platform

| Platform | Extraction | `--source` |
|---|---|---|
| ChatGPT | Settings -> Data export -> `conversations.json` | `chatgpt` |
| Claude | Settings -> Export data -> `conversations.json` | `claude` |
| Gemini | Google Takeout -> save as `.md` | `generic` (Takeout parser = TODO) |
| Perplexity/Grok/DeepSeek/Kimi | copy the page into a `.md` | `generic` |

## Providers for the opinion

`anthropic`, `openai`, `gemini`, `grok`, `perplexity`, and the Chinese ones `deepseek`, `kimi`, `qwen`, `glm`, `minimax`.

**Shortcut:** `openrouter` — one key and one endpoint reach almost every model (including all the Chinese ones); just change `--model` (e.g. `--provider openrouter --model qwen/qwen3-max`). Recommended if you don't want to juggle 6 different base URLs.

Keys go in env vars (see `.env.example`). Model IDs change often: set your own with `--model` or via env.

## Usage

```bash
pip3 install -r requirements.txt
cp .env.example .env   # add your keys
export $(grep -v '^#' .env | xargs)

python3 cli.py list   --source claude  --input conversations.json
python3 cli.py review --source claude  --input conversations.json --which 3      --provider anthropic
python3 cli.py review --source chatgpt --input conversations.json --which 0:10   --provider deepseek
python3 cli.py review --source generic --input mychat.md                         --provider grok
```

Output: one `reviews/NNN_title__review_<provider>.md` file per chat.
The opinion is written in English by default; use `--lang it|nl|fr` to change it.

## Bulk runs and resume (manifest)

When you `review` many chats, each outcome is written to `reviews/_manifest.csv` and `_manifest.json`
(`done` / `failed` with the reason), **after every chat** (if it crashes or you run out of quota, you lose nothing).
Pick up again with `--resume`: it skips the `done` ones and retries the `failed`/missing ones.

```bash
python3 cli.py review --source claude --input conversations.json --which all --provider openrouter
# ran out of quota halfway? same command + --resume
python3 cli.py review --source claude --input conversations.json --which all --provider openrouter --resume
```

## Review prompt

By default it uses an "expert" prompt (read carefully, tell me if you agree, what you'd change, etc.).
You can override it:
- `--prompt "your text"` inline
- `--prompt-file my_prompt.txt`
- if you pass nothing and you're in an interactive terminal, it asks you.

## Attachments (PDF and more)

Attach files to the chat before sending it for review with `--attach` (repeatable).
The file is extracted as **text** (not base64): cheap on tokens and works with every
provider, not only multimodal ones. Supported: `pdf, txt, md, csv, json, docx`.

```bash
python3 cli.py review --source claude --input conversations.json --which 0 \
  --provider gemini --attach dpa.pdf --attach annex.docx
```

Unsupported or unreadable files (e.g. scanned image-only PDFs — no OCR in v1) are
reported and skipped, never fatal. Attachment references found inside an export
(names/ids) are still cited in the chat text, but their binaries are not auto-loaded —
pass the actual file with `--attach`.

Note: there is **no length cap** on the chat sent to the model — long conversations
go through in full (you spend the tokens you need).

## Layout
```
schema.py         common schema (Conversation/Message/Attachment)
ingest/           extraction parsers (chatgpt, claude, generic, stubs)
providers/        API clients for the opinion (anthropic, openai-compat, gemini)
review.py         review prompt + orchestration
cli.py            command-line interface
```

## Roadmap
- Native Google Takeout parser (Gemini).
- Userscript scraper for Perplexity/Grok/Kimi/DeepSeek -> common JSON schema.
- Re-send attachments (images/PDFs) to providers that support them.
