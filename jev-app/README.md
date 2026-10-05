# Jev Runner

A small local web app for running TypeSafe's Jev (System One) model.
You enter an API key, a state and a set of typed questions, and it shows the
typed answers with their probabilities.

```bash
python3 app.py            # then open http://127.0.0.1:8765
python3 app.py --port 9000
```

No packages to install. It needs Python 3.8 or newer.

- **API key:** type it in the form, or `export TYPESAFE_API_KEY=...` before starting. It is never written to disk.
- **State:** a JSON object, or plain text.
- **Questions:** a JSON object. Each entry has a `type` of `choice`, `score` or `noul`, plus `instructions` and optional `criteria`.

The server exists because the Jev API rejects direct calls from browsers on
other origins. It listens on 127.0.0.1 only and forwards each run to
`https://api.typesafe.ai/v1/systemone`.

## Hosted version

The same page is published at https://rajatghosh.me/jev.html (source:
`public/jev.html`). The hosted page has no server, so it only accepts an
OpenRouter API key and calls `https://openrouter.ai/api/v1/systemone` straight
from the browser. Use this local app when you have a TypeSafe API key.
