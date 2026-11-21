#!/usr/bin/env python3
"""Cross-compare original historical agentgrep source behavior and downstream markers."""
import argparse
import hashlib
import json
from pathlib import Path

SCENARIOS = ["HIDDEN_HOLD", "SINGLE_BENIGN", "ZERO", "FIRST_HOLD", "TWO_BENIGN"]
BASE = "9b5ccda643f2bf84c49b0ec1c4ae300b681a5f83"
REPAIRED = "6b2d3465767421f113acf684473384db00ebf619"


def check(value, why):
    if not value:
        raise AssertionError(why)


def read(path, revision, commit):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    check(d["revision"] == revision and d["source"]["source_commit"] == commit,
          "Wrong original commit / experiment side")
    cases = d["cases"]
    check(len(cases) == 10, "Missing cases")
    key = {(x["scenario"], x["consumer"]): x for x in cases}
    check(set(key) == {(s, c) for s in SCENARIOS for c in ("visible", "complete")},
          "Unexpected scenario roster")
    for x in cases:
        check((x["marker_written"] and x["marker_sha256"] is not None) or
              (not x["marker_written"] and x["marker_sha256"] is None),
              "Write marker missing or inconsistent")
        check(x["visited_count"] == sum(map(len, x["all_pages"])), "Visited count mismatch")
    return d, key


def compare(before_path, after_path):
    b, pre = read(before_path, "before", BASE)
    a, post = read(after_path, "after", REPAIRED)
    check(b["summary"]["markers"] == {"visible": 4, "complete": 0},
          "Original pre-fix rule counts differ")
    check(a["summary"]["markers"] == {"visible": 4, "complete": 3},
          "Original post-fix rule counts differ")
    check(b["summary"]["unwarranted_marker_cases"] == ["FIRST_HOLD/visible"],
          "Original first-page source selection changed")
    check(a["summary"]["unwarranted_marker_cases"] == ["HIDDEN_HOLD/visible"],
          "Repaired page selection changed")
    for s in SCENARIOS:
        for consumer in ("visible", "complete"):
            x = pre[(s, consumer)]
            y = post[(s, consumer)]
            known_firsts = {
                "HIDDEN_HOLD": ("serenity HOLD", "serenity cleared"),
                "SINGLE_BENIGN": ("serenity cleared", "serenity cleared"),
                "ZERO": (None, None),
                "FIRST_HOLD": ("serenity cleared", "serenity HOLD"),
                "TWO_BENIGN": ("serenity approved", "serenity cleared"),
            }
            expected_x, expected_y = known_firsts[s]
            check(x["first_page_texts"] == ([] if expected_x is None else [expected_x]),
                  "Original source selection drift: " + s)
            check(y["first_page_texts"] == ([] if expected_y is None else [expected_y]),
                  "Repaired source selection drift: " + s)
            check("query" in x["first_page_keys"] and "status" not in x["first_page_keys"],
                  "Original flat contract changed")
            check(y["first_status"] in ("complete", "bounded"),
                  "Historical repaired status absent")
            check(y["first_cursor_present"] == (s in ("HIDDEN_HOLD", "FIRST_HOLD", "TWO_BENIGN")),
                  "Cursor presence differs from fixed fixture")
            if consumer == "complete":
                check(x["marker_written"] is False, "Old no-evidence case wrote marker")
                check(y["visited_count"] == y["source_match_count"],
                      "Repaired full traversal missed results")
    hidden_pre = pre[("FIRST_HOLD", "visible")]
    hidden_after = post[("HIDDEN_HOLD", "complete")]
    check(hidden_pre["marker_written"] and not hidden_pre["safe_warrant"],
          "Original wrong action witness absent")
    check(hidden_after["all_pages"] == [["serenity cleared"], ["serenity HOLD"]],
          "Actual original cursor did not recover hidden HOLD")
    check(hidden_after["marker_written"] is False, "HOLD marker incorrectly cleared")
    check(post[("SINGLE_BENIGN", "complete")]["marker_written"], "Single benign false-blocked")
    check(post[("ZERO", "complete")]["marker_written"], "Zero-result false-blocked")
    check(post[("TWO_BENIGN", "complete")]["marker_written"], "Two benign false-blocked")
    return {
        "pass": True,
        "project": "tony/agentgrep",
        "source_type": "local Codex JSONL prompt history",
        "external_issue": "https://github.com/tony/agentgrep/issues/55",
        "merged_pull_request": "https://github.com/tony/agentgrep/pull/64",
        "revisions": {"before": BASE, "after": REPAIRED},
        "source_results": {
            "before": b["summary"],
            "after": a["summary"],
        },
        "result": "The pre-merge flat response hides an older matching HOLD record at limit=1. The merged status and cursor allow full traversal and withholding of the test release marker.",
        "scope": "original FastMCP search tool with synthetic source data and study-owned marker writes",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("before")
    p.add_argument("after")
    p.add_argument("--probe-before", required=True)
    p.add_argument("--probe-after", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    result = compare(a.before, a.after)
    bb = json.loads(Path(a.probe_before).read_text())
    aa = json.loads(Path(a.probe_after).read_text())
    assert bb["source"]["source_commit"] == BASE
    assert aa["source"]["source_commit"] == REPAIRED
    expected = ["serenity newest", "serenity middle", "serenity oldest"]
    assert bb["reported_texts"] == [expected[0]]
    assert bb["missing"] == expected[1:]
    assert not bb["complete_source_recovered"]
    assert aa["reported_texts"] == expected
    assert aa["complete_source_recovered"] and aa["ordering_consistent"]
    assert not aa["duplicates"] and not aa["missing"]
    assert [p["status"] for p in aa["pages"]] == ["bounded", "bounded", "complete"]
    result["heldout_three_record_probe"] = {
        "before": {"pages": bb["page_count"], "records": bb["reported_texts"]},
        "after": {"pages": aa["page_count"], "records": aa["reported_texts"]},
        "complete_recovery": True,
    }
    Path(a.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("E5_PAIR_PASS " + json.dumps(result["source_results"], sort_keys=True))


if __name__ == "__main__":
    main()
