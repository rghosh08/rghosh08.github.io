---
title: Von Decision Server
emoji: 🧭
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
short_description: Von System One server behind the Semantic Router page
---

# Von Decision Server

Runs [wfzyx/von](https://huggingface.co/wfzyx/von), an open-source System One
decision model, as its TypeSafe-compatible HTTP server. It backs the
[Semantic Router](https://rajatghosh.me/jev-router.html) page, which asks Von
how hard a coding request is and routes it to the cheapest Claude model that
can handle it.

- `GET /health`
- `POST /v1/systemone` with `{"model": "von-latest", "state": ..., "questions": {...}}`

Built from the upstream `ghcr.io/wfzyx/von:cpu` image. Weights are fetched
from the Hub on each cold start.
