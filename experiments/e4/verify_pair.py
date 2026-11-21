#!/usr/bin/env python3
"""Cross-commit evidence and real HTTP effect controls for the E4 Agno replay."""
import argparse
import hashlib
import json
from pathlib import Path

BEFORE = "bc563b724c2ea39368ca99b6cd45d36a64a7b1c5"
AFTER = "9ff6d911131768470f91620ba40878a1f9372b61"
STATES = ["COMPLETE_EMPTY", "INCOMPLETE_EMPTY", "POSITIVE_HIT", "NEXT_PAGE", "API_FAILURE"]
MODES = ["projection", "coverage"]


def require(value, message):
    if not value:
        raise AssertionError(message)


def index(report):
    rows = report["rows"]
    require(len(rows) == 10, "Each version requires 10 precommitted cases")
    lookup = {(row["state"], row["mode"]): row for row in rows}
    require(set(lookup) == {(state, mode) for state in STATES for mode in MODES},
            "Scenario identity mismatch")
    return lookup


def verify_file(path, commit, revision):
    report = json.loads(path.read_text())
    require(report["source"]["commit"] == commit, "Historical source commit mismatch")
    require(report["revision"] == revision, "Experiment revision mismatch")
    require(report["summary"]["cases"] == 10, "One condition omitted")
    receipts = [json.loads(s) for s in path.with_name(path.stem + "_http_receipts.jsonl").read_text().splitlines()]
    require(receipts == report["receipts"], "HTTP write receipts differ from saved run")
    require(len(receipts) == report["summary"]["write_count"], "Reported write count differs")
    require(len(report["summary"]["controls"]) == 2, "Delegation or async controls absent")
    return report, index(report), receipts


def verify(before_path, after_path):
    b, pre, b_receipts = verify_file(before_path, BEFORE, "before")
    a, post, a_receipts = verify_file(after_path, AFTER, "after")
    require(b["source"]["git_blob"] == "e7bf38548f561d3a5264a8da7e29b4905f17cea4", "Before blob changed")
    require(a["source"]["git_blob"] == "654c4c4697191612f3cd72e32627c3e1a564eeba", "After blob changed")
    for mode in MODES:
        p_complete = pre[("COMPLETE_EMPTY", mode)]
        p_incomplete = pre[("INCOMPLETE_EMPTY", mode)]
        q_complete = post[("COMPLETE_EMPTY", mode)]
        q_incomplete = post[("INCOMPLETE_EMPTY", mode)]
        require(p_complete["returned"] == p_incomplete["returned"], "Before collision missing")
        require(q_complete["returned"] != q_incomplete["returned"], "After distinction missing")
        require(q_complete["returned"]["incompleteSearch"] is False, "Complete signal wrong")
        require(q_incomplete["returned"]["incompleteSearch"] is True, "Incomplete signal wrong")
        for state in STATES:
            x = pre[(state, mode)]
            y = post[(state, mode)]
            require(x["request_corpora"] == y["request_corpora"] == "allDrives", "Corpus drift")
            require("incompleteSearch" not in x["request_fields"], "Before requested new field")
            require("incompleteSearch" in y["request_fields"], "After omitted new field")
            require(x["returned"]["count"] == y["returned"]["count"] if "count" in x["returned"] else
                    "error" in y["returned"], "Unexpected unrelated result-count difference")
    exp = {
        "before": {"projection": 2, "coverage": 0},
        "after": {"projection": 2, "coverage": 1},
    }
    observed = {
        "before": {mode: sum(pre[(s, mode)]["write"] for s in STATES) for mode in MODES},
        "after": {mode: sum(post[(s, mode)]["write"] for s in STATES) for mode in MODES},
    }
    require(observed == exp, "Unexpected effects for frozen E4 design")
    require(b["summary"]["write_count"] == 2, "Before provider effects")
    require(a["summary"]["write_count"] == 3, "After provider effects")
    require(pre[("INCOMPLETE_EMPTY", "projection")]["write"] is True, "Before incomplete effect absent")
    require(post[("INCOMPLETE_EMPTY", "projection")]["write"] is True, "After projection effect absent")
    require(post[("INCOMPLETE_EMPTY", "coverage")]["write"] is False, "After guarded effect occurred")
    require(post[("COMPLETE_EMPTY", "coverage")]["write"] is True, "After valid effect missing")
    for state in ("POSITIVE_HIT", "NEXT_PAGE", "API_FAILURE"):
        for mode in MODES:
            require(not pre[(state, mode)]["write"] and not post[(state, mode)]["write"],
                    "Expected blocked control: " + state)
    return {
        "pass": True,
        "original_issue": "https://github.com/agno-agi/agno/issues/7823",
        "merged_fix": "https://github.com/agno-agi/agno/pull/7824",
        "source_commits": {"before": BEFORE, "after": AFTER},
        "scenario_count": 20,
        "results": observed,
        "provider_receipts": {"before": len(b_receipts), "after": len(a_receipts)},
        "original_search_collision": "complete/incomplete identical before fix; distinct after fix",
        "downstream_constraint": "only coverage-aware consumer blocks partial result after repair",
        "scope": "Local Google API provider, original Agno search/upload methods, deterministic caller",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = verify(Path(args.before), Path(args.after))
    out = Path(args.output)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("E4_PAIR_PASS " + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
