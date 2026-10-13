# Jev Runner

A small local web app for running TypeSafe's Jev (System One) model.
You enter an API key, a state and a set of typed primitives (Choice, Score, Noul), and it shows the
typed answers with their probabilities.

```bash
python3 app.py            # then open http://127.0.0.1:8765
python3 app.py --port 9000
```

No packages to install. It needs Python 3.8 or newer.

- **API key:** type it in the form, or `export TYPESAFE_API_KEY=...` before starting. It is never written to disk.
- **State:** a JSON object, or plain text.
- **Primitives (Choice, Score, Noul):** a JSON object, sent to the API as `questions`. Each entry has a `type` of `choice`, `score` or `noul`, plus `instructions` and optional `criteria`.

The server exists because the Jev API rejects direct calls from browsers on
other origins. It listens on 127.0.0.1 only and forwards each run to
`https://api.typesafe.ai/v1/systemone`.

## Hosted version

The same page is published at https://rajatghosh.me/jev.html (source:
`public/jev.html`). The site is static, so TypeSafe-key requests from the
hosted page go through a small relay in `relay/`, a Netlify function at
`https://jev-relay-rajatghosh.netlify.app/systemone`. The relay only answers
rajatghosh.me, forwards the caller's key in memory, and stores nothing.

```bash
cd relay && netlify deploy --prod --site 8ac1fe44-30c9-47e2-bdb7-c3ec34688af0 \
  --dir "$PWD/site" --functions "$PWD/netlify/functions"
```

The hosted page requires the caller to type a TypeSafe API key. The page also
accepts an OpenRouter API key, which is sent straight from the browser to
`https://openrouter.ai/api/v1/systemone`.

## Von Semantic Router

A second page, `public/jev-router.html`, routes coding requests to the right
Claude model. [Von](https://huggingface.co/wfzyx/von), an open-source
System One decision model (Apache-2.0, 395M parameters, fine-tuned from
ModernBERT-large), scores the request on a three-level difficulty rubric and
returns P(simple), P(medium), P(advanced). The page picks the cheapest tier
whose cumulative probability reaches the coverage threshold (default 0.8), so
uncertain requests escalate instead of landing on a weak model, then streams
that model's answer.

Von has no hosted API, so it runs on your machine. Its `/v1/systemone`
endpoint is wire-compatible with the Jev API, which is why the page needed no
change to its rubric or parsing:

```bash
pip install "von-sdk>=1.3.7"
von serve                 # downloads the weights (about 3 GB) on first run, listens on :8000
# or: docker run --rm -p 8000:8000 -v von-hf:/data/huggingface ghcr.io/wfzyx/von:cpu
```

| Tier   | Model              | max_tokens | effort |
| ------ | ------------------ | ---------- | ------ |
| Low    | `claude-haiku-5-5`  | 8,000      | low    |
| Medium | `claude-sonnet-5-5` | 32,000     | medium |
| High   | `claude-opus-5-5`   | 64,000     | high   |

The page works in two steps. Step 1 routes: Von's probabilities, the
chosen tier, and the raw response are shown, and nothing is sent to Claude.
Step 2 is a separate "Generate answer" button next to a model picker preset
to Von's choice, so the decision can be overridden before any answer is
generated. Editing the request after step 1 requires routing again.

If the Von server is unreachable or returns a server error, the request falls
back to the High tier. A rejected Von API key or a malformed request stops
with an error instead. A tier can also be forced from the form, which skips
Von. The Sonnet and Opus calls send
`fallbacks: "default"` (beta `server-side-fallback-2026-07-01`), so a
safety-classifier refusal is retried on a fallback model server-side.

```bash
python3 router.py         # then open http://127.0.0.1:8766
```

For a one-click session on a Mac, double-click `start-von.command` in
Finder. It starts `von serve` and `router.py` (skipping whichever is already
running), waits for Von, and opens the page. Closing its Terminal window stops
both. The page also shows a Von status line; when served by `router.py` and
Von is not running, a **Start Von** button starts it as a child of the app
server (looked for at `VON_BIN`, then `~/.venvs/von/bin/von`, then on `PATH`),
so it stops when the app server does.

Locally, both calls go through `router.py`. The Von call goes to
`VON_BASE_URL` (default `http://127.0.0.1:8000`) unless the page names
another server, with `VON_API_KEY` as the bearer token when the Von server
is started with one; the Anthropic key field falls back to `ANTHROPIC_API_KEY`.
The hosted copy at https://rajatghosh.me/jev-router.html sends the Von call
from the browser straight to the Von server typed into the page (Von allows
cross-origin calls by default) and the Claude call from the browser straight
to `api.anthropic.com`, using the API's browser-access header. Browsers are
tightening the rules on an https page calling a plain http server on
localhost: Safari blocks it (the fetch fails with "Load failed") and Chrome
142 blocks it under Private Network Access. When that happens the page says
so and points to the local copy at http://127.0.0.1:8766, which works in
every browser because the page and Von are both on localhost. If that direct
call fails at the network level (the browser reports "Failed to fetch",
typically an extension, proxy, or network blocking the host), the page
retries through `relay/netlify/edge-functions/messages.js` at
`https://jev-relay-rajatghosh.netlify.app/messages`, which streams the
response back and notes "via relay" in the status line. It is an Edge
Function because regular Netlify functions stop after 60 seconds, while an
edge function only has to start responding within 40 seconds. The same
`netlify deploy` command above deploys it.

### Command-line version

`claude_tier_router.py` is the same router as a CLI built on the official
`typesafe-sdk` and `anthropic` packages. It still classifies with TypeSafe's
hosted Jev rather than Von. It adds `-f queries.txt` for
classifying a file of requests into JSONL with a tier summary.

```bash
pip install typesafe-sdk anthropic
export TYPESAFE_API_KEY=ts_...  ANTHROPIC_API_KEY=sk-ant-...
python3 claude_tier_router.py "write a regex that matches IPv4 addresses"
python3 claude_tier_router.py --dry-run "design a sharded rate limiter"
python3 -m pytest test_router.py      # offline, mocked HTTP for both APIs
```
