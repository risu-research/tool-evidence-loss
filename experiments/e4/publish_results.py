#!/usr/bin/env python3
"""Publish only the validated E4 experiment data from a successful CI run."""
import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from verify_pair import verify

NAMES = (
    "e4_before.json",
    "e4_after.json",
    "e4_verification.json",
    "e4_before_http_receipts.jsonl",
    "e4_after_http_receipts.jsonl",
    "e4_discovery_before.json",
    "e4_discovery_after.json",
)
DENY = re.compile(
    r"(?i)github_pat_|ghp_[A-Za-z0-9]{10,}|sk-proj-|"
    r"PRIVATE KEY|hotmail\.com|/home/runner/|C:\\Users\\|/mnt/data/"
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(source):
    pair = verify(source / "e4_before.json", source / "e4_after.json")
    independent = json.loads((source / "e4_verification.json").read_text())
    assert independent == pair, "Cross-version report differs from fresh verification"
    before = json.loads((source / "e4_discovery_before.json").read_text())
    after = json.loads((source / "e4_discovery_after.json").read_text())
    assert before["pass"] and after["pass"]
    assert before["revision"] == "before"
    assert after["revision"] == "after"
    assert before["states"][0]["tool_result"] == before["states"][1]["tool_result"]
    assert after["states"][0]["tool_result"] != after["states"][1]["tool_result"]
    assert before["source"]["commit"] == pair["source_commits"]["before"]
    assert after["source"]["commit"] == pair["source_commits"]["after"]
    for name in NAMES:
        content = (source / name).read_text(encoding="utf-8")
        assert not DENY.search(content), f"Disclosure pattern in {name}"
        if name.endswith(".json"):
            json.loads(content)
        else:
            assert len(content.splitlines()) in (2, 3), f"Receipt count changed: {name}"
            for line in content.splitlines():
                json.loads(line)
    return pair


def publish(source, dest):
    report = validate(source)
    dest.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        shutil.copyfile(source / name, dest / name)
    provenance = {
        "experiment": "E4 Agno historical repair replay",
        "github_actions_run": os.environ.get("GITHUB_RUN_ID", ""),
        "experiment_input_commit": os.environ.get("GITHUB_SHA", ""),
        "upstream_before": report["source_commits"]["before"],
        "upstream_after": report["source_commits"]["after"],
        "scenarios": report["scenario_count"],
        "provider_effects": report["provider_receipts"],
        "evidence_files": {name: sha(dest / name) for name in NAMES},
    }
    (dest / "RUN_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [f"{sha(dest / name)}  {name}" for name in (*NAMES, "RUN_PROVENANCE.json")]
    (dest / "SHA256SUMS.txt").write_text("\n".join(sorted(lines)) + "\n")
    print(json.dumps({"pass": True, "published_files": len(NAMES) + 2,
                      "summaries": report["results"]}, sort_keys=True))


def check_published(source, dest):
    validate(source)
    items = (dest / "SHA256SUMS.txt").read_text().splitlines()
    assert len(items) == len(NAMES) + 1
    for entry in items:
        expected, relative = entry.split("  ", 1)
        p = (dest / relative).resolve()
        assert p.is_relative_to(dest.resolve()) and p.is_file()
        assert sha(p) == expected, f"Archive hash changed: {relative}"
    expected = json.loads((dest / "e4_verification.json").read_text())
    fresh = json.loads((source / "e4_verification.json").read_text())
    assert expected == fresh, "Historical observations changed"
    print("E4_ARCHIVE_VERIFIED", json.dumps(expected["results"], sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="results")
    parser.add_argument("--dest", default="evidence/e4")
    parser.add_argument("--check", action="store_true")
    a = parser.parse_args()
    if a.check:
        check_published(Path(a.source), Path(a.dest))
    else:
        publish(Path(a.source), Path(a.dest))


if __name__ == "__main__":
    main()
