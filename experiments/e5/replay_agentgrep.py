#!/usr/bin/env python3
"""Original agentgrep MCP page-boundary replay using synthetic local Codex records."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SOURCE_COMMITS = {
    "before": {
        "commit": "9b5ccda643f2bf84c49b0ec1c4ae300b681a5f83",
        "search_blob": "61d8f7837bef4ab35b91044b46e78e3f8e3fa197",
    },
    "after": {
        "commit": "6b2d3465767421f113acf684473384db00ebf619",
        "search_blob": "14da30d259562549038e805de760359a9120e7b5",
    },
}
TESTS = {
    "HIDDEN_HOLD": [
        ("new", "2026-01-02T00:00:00Z", "serenity cleared"),
        ("old", "2026-01-01T00:00:00Z", "serenity HOLD"),
    ],
    "SINGLE_BENIGN": [
        ("new", "2026-01-02T00:00:00Z", "serenity cleared"),
    ],
    "ZERO": [
        ("new", "2026-01-02T00:00:00Z", "different topic"),
    ],
    "FIRST_HOLD": [
        ("new", "2026-01-02T00:00:00Z", "serenity HOLD"),
        ("old", "2026-01-01T00:00:00Z", "serenity cleared"),
    ],
    "TWO_BENIGN": [
        ("new", "2026-01-02T00:00:00Z", "serenity cleared"),
        ("old", "2026-01-01T00:00:00Z", "serenity approved"),
    ],
}
EXPECTED = {
    "before": {"visible": 4, "complete": 0},
    "after": {"visible": 4, "complete": 3},
}


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise AssertionError(msg)


def checkout_identity(checkout: Path, version: str) -> dict[str, Any]:
    expect = SOURCE_COMMITS[version]
    commit = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()
    require(commit == expect["commit"], f"Original commit changed: {commit}")
    origin = checkout / "src/agentgrep/mcp/tools/search_tools.py"
    data = origin.read_bytes()
    blob = hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()
    require(blob == expect["search_blob"], f"Historical MCP source blob changed: {blob}")
    return {
        "source_repo": "https://github.com/tony/agentgrep",
        "source_commit": commit,
        "source_file": "src/agentgrep/mcp/tools/search_tools.py",
        "source_blob": blob,
        "source_sha256": hashlib.sha256(data).hexdigest(),
    }


def fixture(root: Path, case: str) -> Path:
    home = root / "home"
    sessions = home / ".codex" / "sessions" / "2026" / "01" / "01"
    sessions.mkdir(parents=True, exist_ok=True)
    for name, timestamp, text in TESTS[case]:
        path = sessions / (name + ".jsonl")
        records = [
            {
                "type": "session_meta",
                "payload": {"id": "synthetic-" + name, "model_provider": "openai"},
            },
            {
                "timestamp": timestamp,
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": text}],
                },
            },
        ]
        path.write_text("\n".join(json.dumps(x) for x in records) + "\n", encoding="utf-8")
    return home


def payload(result: Any) -> dict[str, Any]:
    require(not bool(getattr(result, "is_error", False)), "MCP returned error")
    content = result.content
    require(bool(content), "MCP result has empty content")
    data = json.loads(content[0].text or "")
    require(isinstance(data, dict), "MCP JSON response shape")
    return data


async def replay_case(version: str, name: str, rule: str) -> dict[str, Any]:
    from fastmcp import Client
    from agentgrep.mcp import build_mcp_server

    with tempfile.TemporaryDirectory(prefix="e5-agentgrep-") as tmp:
        root = Path(tmp)
        home = fixture(root, name)
        old_home = os.environ.get("HOME")
        os.environ["HOME"] = str(home)
        try:
            async with Client(build_mcp_server()) as mcp:
                all_tools = await mcp.list_tools()
                require(any(t.name == "search" for t in all_tools), "Original search unavailable")
                first = payload(
                    await mcp.call_tool(
                        "search",
                        {
                            "terms": ["serenity"],
                            "agent": "codex",
                            "scope": "prompts",
                            "limit": 1,
                        },
                    )
                )
                texts = [x["text"] for x in first["results"]]
                require(len(texts) <= 1, "Original search exceeded requested page size")
                pages = [texts]
                status = first.get("status")
                info = first.get("page")
                cursor = info.get("next_cursor") if isinstance(info, dict) else None
                first_keys = sorted(first.keys())
                first_state = status.get("state") if isinstance(status, dict) else None
                expected_page = len(TESTS[name]) if name != "ZERO" else 0
                if name in ("HIDDEN_HOLD", "FIRST_HOLD", "TWO_BENIGN"):
                    require(len(texts) == 1, "Two-hit fixture produced unexpected first page")
                elif name == "SINGLE_BENIGN":
                    require(len(texts) == 1, "Single-hit fixture missing first page")
                else:
                    require(len(texts) == 0, "Unmatched fixture returned results")
                if version == "before":
                    require(info is None and status is None, "Pre-repair completion signal appeared")
                else:
                    require(isinstance(info, dict), "Post-repair page envelope absent")
                    require(isinstance(status, dict), "Post-repair status absent")
                    require(info["count"] == len(texts), "Post-repair page count mismatch")
                    require(
                        (first_state == "bounded") == (expected_page == 2),
                        "Post-repair page status inconsistent with known fixture",
                    )
                    require(
                        bool(cursor) == (expected_page == 2),
                        "Post-repair continuation cursor missing or spurious",
                    )
                if rule == "visible":
                    allow = not any("HOLD" in text for text in texts)
                    decision_reason = "visible_first_page"
                else:
                    require(rule == "complete", "Unknown consumer mode")
                    if status is None:
                        allow = False
                        decision_reason = "no_completion_evidence"
                    else:
                        while status.get("state") == "bounded":
                            require(bool(cursor), "Bounded status lacks cursor")
                            require(len(pages) <= 3, "Pagination did not terminate")
                            next_data = payload(await mcp.call_tool("search", {"cursor": cursor}))
                            next_texts = [x["text"] for x in next_data["results"]]
                            require(not set(next_texts).intersection(set().union(*[set(p) for p in pages])),
                                    "Continuation repeated a prior record")
                            pages.append(next_texts)
                            status = next_data.get("status")
                            info = next_data.get("page")
                            require(isinstance(info, dict) and isinstance(status, dict),
                                    "Continuation lost status")
                            cursor = info.get("next_cursor")
                        require(status.get("state") == "complete" and cursor is None,
                                "Complete result state absent after traversal")
                        whole = [text for page in pages for text in page]
                        require(len(whole) == expected_page,
                                "Full traversal omitted a known synthetic source match")
                        allow = not any("HOLD" in text for text in whole)
                        decision_reason = "complete_coverage"
                output = root / ("release-marker-" + rule + ".json")
                if allow:
                    receipt = {"fixture": name, "consumer": rule, "approved": True}
                    encoded = json.dumps(receipt, sort_keys=True).encode("utf-8")
                    with output.open("xb") as file:
                        file.write(encoded)
                        file.flush()
                        os.fsync(file.fileno())
                    require(output.read_bytes() == encoded, "Persisted release marker unreadable")
                    content_sha = hashlib.sha256(output.read_bytes()).hexdigest()
                else:
                    require(not output.exists(), "Write occurred under a blocked decision")
                    content_sha = None
                return {
                    "scenario": name,
                    "consumer": rule,
                    "first_page_texts": texts,
                    "first_page_keys": first_keys,
                    "first_status": first_state,
                    "first_cursor_present": bool(info if False else first.get("page", {}).get("next_cursor")) if version == "after" else False,
                    "all_pages": pages,
                    "visited_count": sum(len(p) for p in pages),
                    "source_match_count": expected_page,
                    "marker_written": allow,
                    "marker_sha256": content_sha,
                    "decision": decision_reason,
                    "safe_warrant": "HOLD" not in [text for _, _, text in TESTS[name]],
                }
        finally:
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home


async def run_all(version: str, identity: dict[str, Any]) -> dict[str, Any]:
    entries = []
    for case in TESTS:
        for rule in ("visible", "complete"):
            entries.append(await replay_case(version, case, rule))
    assert len(entries) == 10
    observed = {rule: sum(x["marker_written"] for x in entries if x["consumer"] == rule)
                for rule in ("visible", "complete")}
    require(observed == EXPECTED[version], f"Precommitted expected outcomes failed {observed}")
    unwarranted = [
        x["scenario"] + "/" + x["consumer"] for x in entries
        if x["marker_written"] and not x["safe_warrant"]
    ]
    require(unwarranted == ["HIDDEN_HOLD/visible"], "Unexpected unsafe marker writes")
    return {
        "source": identity,
        "revision": version,
        "fixture_count": len(TESTS),
        "cases": entries,
        "summary": {
            "conditions": len(entries),
            "markers": observed,
            "unwarranted_marker_cases": unwarranted,
            "all_marker_count": sum(observed.values()),
        },
        "scope": "original FastMCP server and search tool on synthetic Codex history",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--revision", choices=("before", "after"), required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    checkout = Path(args.source).resolve()
    identity = checkout_identity(checkout, args.revision)
    sys.path.insert(0, str(checkout / "src"))
    import agentgrep
    require(
        Path(agentgrep.__file__).resolve().is_relative_to(checkout / "src"),
        "Loaded agentgrep from another revision",
    )
    out = asyncio.run(run_all(args.revision, identity))
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "E5_REPLAY_PASS "
        + json.dumps(
            {"source": identity["source_commit"], "revision": args.revision, **out["summary"]},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
