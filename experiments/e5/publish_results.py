#!/usr/bin/env python3
"""Archive narrowly scoped synthetic E5 research evidence from verified GitHub Actions."""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

from verify_pair import compare

FILES = [
    "e5_before.json",
    "e5_after.json",
    "e5_pair.json",
    "e5_probe_before.json",
    "e5_probe_after.json",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(source):
    actual = compare(source / "e5_before.json", source / "e5_after.json")
    recorded = json.loads((source / "e5_pair.json").read_text())
    for key in ("pass", "revisions", "source_results", "result"):
        assert actual[key] == recorded[key], f"Historical result mismatch: {key}"
    bb = json.loads((source / "e5_probe_before.json").read_text())
    aa = json.loads((source / "e5_probe_after.json").read_text())
    assert bb["source"]["source_commit"] == actual["revisions"]["before"]
    assert aa["source"]["source_commit"] == actual["revisions"]["after"]
    assert bb["reported_texts"] == ["serenity newest"]
    assert bb["missing"] == ["serenity middle", "serenity oldest"]
    assert aa["reported_texts"] == ["serenity newest", "serenity middle", "serenity oldest"]
    assert [x["status"] for x in aa["pages"]] == ["bounded", "bounded", "complete"]
    assert aa["complete_source_recovered"] and not aa["duplicates"]
    for name in FILES:
        obj = json.loads((source / name).read_text())
        text = json.dumps(obj, ensure_ascii=False)
        for denied in ("hotmail.com", "github_pat_", "sk-proj-", "PRIVATE KEY"):
            assert denied not in text, f"Sensitive string in output: {name}"
        # Files and source roots are ephemeral during execution. The published
        # summaries contain only the synthetic tokens and source identities.
        assert len(text) < 50000, f"Unexpected oversized output: {name}"
    return actual


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--dest", required=True)
    args = parser.parse_args()
    src, dst = Path(args.source), Path(args.dest)
    result = validate(src)
    dst.mkdir(parents=True, exist_ok=True)
    for filename in FILES:
        shutil.copyfile(src / filename, dst / filename)
    metadata = {
        "study": "S2AI E5 independent source MCP paging",
        "source": "https://github.com/tony/agentgrep",
        "github_actions_run": os.environ.get("GITHUB_RUN_ID", ""),
        "test_commit": os.environ.get("GITHUB_SHA", ""),
        "historical_commits": result["revisions"],
        "conditions": 20,
        "heldout_source_records": 3,
        "file_sha256": {f: digest(dst / f) for f in FILES},
    }
    (dst / "RUN_PROVENANCE.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("E5_PUBLISHED_EVIDENCE " + json.dumps({
        "pass": True, "files": len(FILES) + 1,
        "before": result["source_results"]["before"],
        "after": result["source_results"]["after"],
    }, sort_keys=True))


if __name__ == "__main__":
    run()
