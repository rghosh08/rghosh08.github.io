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

The page also accepts an OpenRouter API key, which is sent straight from the
browser to `https://openrouter.ai/api/v1/systemone`.
