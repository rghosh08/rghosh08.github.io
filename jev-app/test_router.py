"""End-to-end offline test: real typesafe-sdk + anthropic SDKs, mocked HTTP for both."""

import io
import json
import sys

import anthropic
import httpx2
import pytest
from typesafe_sdk import TypeSafeClient

from claude_tier_router import main, Decision, MODELS


def jev_client(p0, p1, p2, fail=False):
    def handle(req):
        if fail:
            return httpx2.Response(500, json={"error": "boom"})
        ans = {
            "type": "score",
            "score": p1 + 2 * p2,
            "confidence": max(p0, p1, p2),
            "legend": {"0": "s", "1": "m", "2": "a"},
            "probabilities": {"0": p0, "1": p1, "2": p2},
        }
        return httpx2.Response(
            200,
            json={"model": "jev-latest", "usage": {}, "answers": {"difficulty": ans}},
        )

    return TypeSafeClient(
        api_key="ts_test", transport=httpx2.MockTransport(handle), retry=None
    )


def sse(text, model):
    events = [
        (
            "message_start",
            {
                "type": "message_start",
                "message": {
                    "id": "msg_1",
                    "type": "message",
                    "role": "assistant",
                    "model": model,
                    "content": [],
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {"input_tokens": 12, "output_tokens": 0},
                },
            },
        ),
        (
            "content_block_start",
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
        ),
        (
            "content_block_delta",
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": text},
            },
        ),
        ("content_block_stop", {"type": "content_block_stop", "index": 0}),
        (
            "message_delta",
            {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                "usage": {"output_tokens": 5},
            },
        ),
        ("message_stop", {"type": "message_stop"}),
    ]
    return "".join(f"event: {e}\ndata: {json.dumps(d)}\n\n" for e, d in events)


def claude_client(seen):
    def handle(req):
        body = json.loads(req.content)
        seen.append(body)
        return httpx2.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text=sse(f"answer from {body['model']}", body["model"]),
        )

    return anthropic.Anthropic(
        api_key="sk-test",
        http_client=httpx2.Client(transport=httpx2.MockTransport(handle)),
    )


@pytest.mark.parametrize(
    "probs, model, effort",
    [
        ((0.9, 0.08, 0.02), "claude-haiku-5-5", "low"),
        ((0.6, 0.3, 0.1), "claude-sonnet-5-5", "medium"),
        ((0.4, 0.3, 0.3), "claude-opus-5-5", "high"),
    ],
)
def test_end_to_end(probs, model, effort):
    seen, out = [], io.StringIO()
    rc = main(
        ["write", "a", "regex"],
        jev=jev_client(*probs),
        claude=claude_client(seen),
        out=out,
    )
    assert rc == 0
    assert out.getvalue().strip() == f"answer from {model}"
    req = seen[0]
    assert req["model"] == model and req["output_config"] == {"effort": effort}
    assert req["messages"] == [{"role": "user", "content": "write a regex"}]
    assert req["stream"] is True


def test_dry_run_makes_no_claude_call():
    seen = []
    main(
        ["--dry-run", "q"], jev=jev_client(0.9, 0.05, 0.05), claude=claude_client(seen)
    )
    assert seen == []


def test_jev_failure_escalates_to_opus():
    seen = []
    main(
        ["q"],
        jev=jev_client(0, 0, 0, fail=True),
        claude=claude_client(seen),
        out=io.StringIO(),
    )
    assert seen[0]["model"] == "claude-opus-5-5"


def test_forced_tier_skips_jev():
    seen = []
    main(
        ["--tier", "simple", "q"],
        jev=jev_client(0, 0, 1, fail=True),
        claude=claude_client(seen),
        out=io.StringIO(),
    )
    assert seen[0]["model"] == "claude-haiku-5-5"


def test_file_mode_jsonl(tmp_path):
    f = tmp_path / "q.txt"
    f.write_text("a\n\nb\n")
    out = io.StringIO()
    main(["-f", str(f)], jev=jev_client(0.1, 0.8, 0.1), out=out)
    rows = [json.loads(line) for line in out.getvalue().splitlines()]
    assert [r["query"] for r in rows] == ["a", "b"]
    assert all(
        r["tier"] == "medium" and r["model"] == "claude-sonnet-5-5" for r in rows
    )
