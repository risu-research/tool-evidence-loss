#!/usr/bin/env python3
"""Independent, held-out three-hit pagination integrity probe for original agentgrep."""
import argparse
import asyncio
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

from replay_agentgrep import checkout_identity, fixture, TESTS, payload


async def run_probe(checkout: Path, revision: str) -> dict:
    from fastmcp import Client
    from agentgrep.mcp import build_mcp_server

    # A held-out local source fixture: oldest, middle, newest.
    # The source-file names and timestamps are explicit so actual source order
    # and cursor results can be inspected without any private user history.
    original = TESTS.copy()
    TESTS["THREE_HIT_PROBE"] = [
        ("a-old", "2026-01-01T00:00:00Z", "serenity oldest"),
        ("b-middle", "2026-01-02T00:00:00Z", "serenity middle"),
        ("c-new", "2026-01-03T00:00:00Z", "serenity newest"),
    ]
    home_saved = os.environ.get("HOME")
    pages = []
    try:
        with tempfile.TemporaryDirectory(prefix="e5-three-") as tmp:
            home = fixture(Path(tmp), "THREE_HIT_PROBE")
            os.environ["HOME"] = str(home)
            async with Client(build_mcp_server()) as client:
                first = payload(await client.call_tool("search", {
                    "terms": ["serenity"], "agent": "codex", "scope": "prompts", "limit": 1,
                }))
                result = first
                seen_cursors = set()
                for step in range(6):
                    texts = [r["text"] for r in result["results"]]
                    page = result.get("page") or {}
                    status = result.get("status") or {}
                    cursor = page.get("next_cursor")
                    pages.append({
                        "index": step,
                        "texts": texts,
                        "status": status.get("state"),
                        "reason": status.get("reason"),
                        "cursor_present": bool(cursor),
                        "stats": result.get("stats", {}),
                    })
                    if not cursor:
                        break
                    if cursor in seen_cursors:
                        pages[-1]["cursor_repeat"] = True
                        break
                    seen_cursors.add(cursor)
                    result = payload(await client.call_tool("search", {"cursor": cursor}))
    finally:
        TESTS.clear()
        TESTS.update(original)
        if home_saved is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = home_saved
    all_texts = [t for page in pages for t in page["texts"]]
    correct = ["serenity newest", "serenity middle", "serenity oldest"]
    return {
        "revision": revision,
        "source": checkout_identity(checkout, revision),
        "known_source_order_newest_first": correct,
        "page_count": len(pages),
        "pages": pages,
        "reported_texts": all_texts,
        "unique_record_count": len(set(all_texts)),
        "duplicates": sorted({x for x in all_texts if all_texts.count(x) > 1}),
        "missing": sorted(set(correct) - set(all_texts)),
        "ordering_consistent": all_texts == correct,
        "complete_source_recovered": sorted(set(all_texts)) == sorted(correct),
        "scope": "original FastMCP tool; synthetic local three-record Codex sessions",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--revision", choices=("before", "after"), required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    checkout = Path(a.source).resolve()
    source = checkout_identity(checkout, a.revision)
    sys.path.insert(0, str(checkout / "src"))
    import agentgrep
    assert Path(agentgrep.__file__).resolve().is_relative_to(checkout / "src")
    report = asyncio.run(run_probe(checkout, a.revision))
    target = Path(a.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("E5_LONG_PAGING_PROBE " + json.dumps({
        "revision": a.revision, "pages": report["pages"],
        "duplicates": report["duplicates"], "missing": report["missing"],
        "ordering_consistent": report["ordering_consistent"],
        "complete_source_recovered": report["complete_source_recovered"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
