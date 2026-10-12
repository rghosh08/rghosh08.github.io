#!/usr/bin/env python3
"""Route coding queries to Claude Haiku / Sonnet / Opus, with Jev judging difficulty.

Jev (TypeSafe) scores each query on a 3-level difficulty rubric and returns calibrated
P(simple), P(medium), P(advanced). We send the query to the cheapest tier whose
cumulative probability P(difficulty <= tier) reaches --coverage, so uncertain queries
escalate instead of failing on a weak model.

Setup:
    pip install typesafe-sdk anthropic
    export TYPESAFE_API_KEY=ts_...  ANTHROPIC_API_KEY=sk-ant-...

Usage:
    python claude_tier_router.py "write a regex that matches IPv4 addresses"
    echo "why does my asyncio.gather hang?" | python claude_tier_router.py
    python claude_tier_router.py --dry-run "design a sharded rate limiter"
    python claude_tier_router.py -f queries.txt     # classify a file, JSONL + tier summary
"""

from __future__ import annotations

import argparse
import json
import sys
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from itertools import accumulate
from typing import TextIO

import anthropic
from typesafe_sdk import Score, TypeSafeClient, TypeSafeError

TIERS = ("simple", "medium", "advanced")

# tier -> (model, max_tokens, effort). Thinking counts toward max_tokens, so leave room.
MODELS = {
    "simple": ("claude-haiku-5-5", 8_000, "low"),
    "medium": ("claude-sonnet-5-5", 32_000, "medium"),
    "advanced": ("claude-opus-5-5", 64_000, "high"),
}

RUBRIC = [
    (
        "Simple: one-liners, syntax or API lookups, explaining a short snippet, a regex "
        "or shell command, a small self-contained function with obvious logic."
    ),
    (
        "Medium: debugging from a stack trace, writing tests, single-file refactors, "
        "standard algorithms and data structures, integrating a known library or API."
    ),
    (
        "Advanced: multi-file or architectural design, concurrency, performance or "
        "memory optimization, GPU kernels, distributed systems, security-sensitive "
        "code, subtle algorithms with many edge cases, or long multi-step reasoning."
    ),
]

INSTRUCTIONS = (
    "Rate the minimum coding-model capability needed to answer this request correctly "
    "on the first try. Judge the task's difficulty, not its length."
)


@dataclass(frozen=True)
class Decision:
    tier: str
    model: str
    expected: float  # probability-weighted level, 0..2 (-1 if Jev failed)
    confidence: float
    probabilities: dict[str, float]


def pick_tier(probs: dict[str, float], coverage: float) -> str:
    cumulative = accumulate(probs.get(t, 0.0) for t in TIERS)
    return next((t for t, c in zip(TIERS, cumulative) if c >= coverage), TIERS[-1])


def classify(jev: TypeSafeClient, query: str, coverage: float) -> Decision:
    try:
        resp = jev.system_one(
            state=query,
            questions={"difficulty": Score(criteria=RUBRIC, instructions=INSTRUCTIONS)},
        )
    except TypeSafeError as e:  # router down: fail safe to the strongest model
        print(f"warning: Jev failed ({e}); using {TIERS[-1]}", file=sys.stderr)
        return Decision(TIERS[-1], MODELS[TIERS[-1]][0], -1.0, 0.0, {})
    a = resp.scores["difficulty"]
    probs = {TIERS[int(k)]: p for k, p in a.probabilities.items()}
    tier = pick_tier(probs, coverage)
    return Decision(tier, MODELS[tier][0], a.score, a.confidence, probs)


def answer(claude: anthropic.Anthropic, tier: str, query: str, out: TextIO) -> str:
    """Stream the chosen model's reply to `out`; return the full text."""
    model, max_tokens, effort = MODELS[tier]
    with claude.messages.stream(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": query}],
        output_config={ "effort": effort },
    ) as stream:
        for text in stream.text_stream:
            out.write(text)
            out.flush()
        final = stream.get_final_message()
    out.write("\n")
    u = final.usage
    print(f"[{model}] in={u.input_tokens} out={u.output_tokens}", file=sys.stderr)
    return "".join(b.text for b in final.content if b.type == "text")


def describe(d: Decision) -> str:
    probs = " ".join(f"{t}={d.probabilities.get(t, 0):.2f}" for t in TIERS)
    return f"[tier={d.tier} model={d.model} {probs} conf={d.confidence:.2f}]"


def main(argv=None, jev=None, claude=None, out: TextIO = sys.stdout) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("query", nargs="*", help="the coding query (or pipe it on stdin)")
    p.add_argument("-f", "--file", help="classify one query per line; prints JSONL")
    p.add_argument("--coverage", type=float, default=0.8, help="default: 0.8")
    p.add_argument(
        "--dry-run", action="store_true", help="classify only, no Claude call"
    )
    p.add_argument("--tier", choices=TIERS, help="skip Jev and force a tier")
    p.add_argument("--workers", type=int, default=8, help="parallelism for -f")
    args = p.parse_args(argv)
    if not 0 < args.coverage <= 1:
        p.error("--coverage must be in (0, 1]")

    ts_key = os.environ.get("TYPESAFE_API_KEY")
    ant_key = os.environ.get("ANTHROPIC_API_KEY")

    jev = jev or TypeSafeClient(api_key=ts_key)

    if args.file:
        with open(args.file) as fh:
            queries = [line.strip() for line in fh if line.strip()]
        with ThreadPoolExecutor(args.workers) as ex:
            decisions = list(ex.map(lambda q: classify(jev, q, args.coverage), queries))
        out.writelines(
            json.dumps({"query": q, **asdict(d)}) + "\n"
            for q, d in zip(queries, decisions)
        )
        counts = Counter(d.tier for d in decisions)
        print(" ".join(f"{t}={counts[t]}" for t in TIERS), file=sys.stderr)
        return 0

    query = " ".join(args.query) or sys.stdin.read().strip()
    if not query:
        p.error("no query given")

    if args.tier:
        d = Decision(args.tier, MODELS[args.tier][0], -1.0, 1.0, {})
    else:
        d = classify(jev, query, args.coverage)
    print(describe(d), file=sys.stderr)
    if args.dry_run:
        return 0

    answer(claude or anthropic.Anthropic(api_key=ant_key), d.tier, query, out)
    return 0


if __name__ == "__main__":
    main()
