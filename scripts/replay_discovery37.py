#!/usr/bin/env python3
"""Independent replay of Table II from the pinned ClosureProbe observation corpus."""
import argparse
import copy
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "experiments/discovery37/source/cases.json"
SOURCE_SHA256 = "f1d0fd842738a74eb30978164cd68500fa11a30af2d7899a50ef0dd23f19e70a"
SOURCE_GIT_BLOB = "f262f6150d8fc97249e88f01d6db1f914d7d1b82"
SOURCE_COMMIT = "12fae2c0cb0909a43f487323fb00e7372b1f3377"
EXPECTED_COUNTS = {
    "R0": (36, 9, 27),
    "R1": (34, 9, 25),
    "R2": (23, 9, 14),
    "R3": (19, 9, 10),
    "RQ": (9, 9, 0),
}
EXPECTED_PROFILES = {
    "generic-enumeration": 6,
    "google-drive-files-list": 6,
    "aws-dynamodb-query": 5,
    "elasticsearch-search-zero": 8,
    "graphql-relay-forward-connection": 5,
    "microsoft-graph-delta-traversal": 7,
}
FIELDS = (
    "case_id", "source_profile", "source_license", "source_branch",
    "empty_visible", "execution_ok", "root_request",
    "final_segment", "reported_zero",
    "R0", "R1", "R2", "R3", "RQ",
)

def fail(message):
    raise ValueError(message)

def check(condition, message):
    if not condition:
        fail(message)

def inspect_bytes():
    data = CORPUS.read_bytes()
    check(hashlib.sha256(data).hexdigest() == SOURCE_SHA256, "Frozen corpus SHA-256 changed")
    actual_git_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    check(actual_git_blob == SOURCE_GIT_BLOB, "Frozen corpus Git blob changed")
    schema = ROOT / "experiments/discovery37/source/corpus.schema.json"
    license_path = ROOT / "experiments/discovery37/source/UPSTREAM_LICENSE.txt"
    check(hashlib.sha256(schema.read_bytes()).hexdigest() ==
          "b872ffc88a3f0e32b1af8eb2370279aeadfef305488bfc577b8cda3746a91934", "Source schema changed")
    check(hashlib.sha256(license_path.read_bytes()).hexdigest() ==
          "7d8fb569801df15ded2684780ee4f3c7135dd72d3d504b9b4957b2ec95a13ead", "Source license changed")
    return json.loads(data)

def latest_page(response, field="response"):
    pages = response.get("pages")
    return pages[-1][field] if pages else response

def array(object_, key):
    value = object_.get(key, [])
    check(isinstance(value, list), f"Expected list at {key}")
    return value

def project(case):
    """Compute the five generic observable predicates using source data alone.

    R2 deliberately checks initial/final status, omitting intermediary token
    continuity. R3 adds observed cardinality, leaving profile-specific validity
    and source qualification outside its projection.
    """
    profile = case["profileId"]
    request, response = case["request"], case["response"]
    check(isinstance(request, dict) and isinstance(response, dict), "Invalid source record")

    if profile == "generic-enumeration":
        visible = array(response, "items")
        empty = len(visible) == 0
        execution = response.get("execution") == "success"
        root = "cursor" not in request and response.get("traversalStatus") != "segment_only"
        final = response.get("continuation") == "exhausted"
        zero = empty

    elif profile == "google-drive-files-list":
        pages = response.get("pages")
        last = latest_page(response)
        visible = array(last, "files")
        all_items = [item for p in pages for item in array(p["response"], "files")] if pages else visible
        empty = len(visible) == 0
        execution = True
        root = "pageToken" not in request
        if pages:
            root = root and "pageToken" not in pages[0]["request"]
        final = not bool(last.get("nextPageToken"))
        zero = len(all_items) == 0

    elif profile == "aws-dynamodb-query":
        pages = response.get("pages")
        last = latest_page(response)
        visible = array(last, "Items")
        all_items = [item for p in pages for item in array(p["response"], "Items")] if pages else visible
        counts = [p["response"].get("Count") for p in pages] if pages else [response.get("Count")]
        empty = len(visible) == 0
        execution = True
        root = "ExclusiveStartKey" not in request
        if pages:
            root = root and "ExclusiveStartKey" not in pages[0]["request"]
        final = not bool(last.get("LastEvaluatedKey"))
        zero = len(all_items) == 0 and all(x in (None, 0) for x in counts)

    elif profile == "elasticsearch-search-zero":
        visible = array(response.get("hits", {}), "hits")
        total = response.get("hits", {}).get("total", {})
        empty = len(visible) == 0
        execution = "error" not in response
        root = True
        final = True
        zero = total.get("value") == 0 and total.get("relation") == "eq"

    elif profile == "graphql-relay-forward-connection":
        result = response.get("data", {}).get("search", {})
        visible = array(result, "edges")
        query = request.get("query", "")
        empty = len(visible) == 0
        execution = not bool(response.get("errors"))
        root = (
            "before:" not in query and
            "last:" not in query and
            not bool(request.get("variables", {}).get("after"))
        )
        final = result.get("pageInfo", {}).get("hasNextPage") is False
        zero = empty

    elif profile == "microsoft-graph-delta-traversal":
        pages = array(response, "pages")
        check(bool(pages), "Graph delta traversal needs pages")
        last = pages[-1]["response"]
        visible = array(last, "value")
        all_items = [item for p in pages for item in array(p["response"], "value")]
        empty = len(visible) == 0
        execution = True
        root = "$skiptoken=" not in request.get("url", "")
        if pages:
            root = root and "$skiptoken=" not in pages[0]["requestUrl"]
        final = not bool(last.get("@odata.nextLink"))
        zero = len(all_items) == 0

    else:
        fail("Unsupported source profile: " + str(profile))

    return {
        "empty_visible": bool(empty),
        "execution_ok": bool(execution),
        "root_request": bool(root),
        "final_segment": bool(final),
        "reported_zero": bool(zero),
    }

def row(case):
    predicates = project(case)
    expected = case["expected"]
    check(expected.get("negativeLicense") in
          {"licensed", "not_licensed", "not_applicable"}, "Unknown frozen license")
    r0 = predicates["empty_visible"]
    r1 = r0 and predicates["execution_ok"]
    r2 = r1 and predicates["root_request"] and predicates["final_segment"]
    r3 = r2 and predicates["reported_zero"]
    rq = expected["negativeLicense"] == "licensed"
    return {
        "case_id": case["id"],
        "source_profile": case["profileId"],
        "source_license": expected["negativeLicense"],
        "source_branch": expected["branch"],
        **predicates,
        "R0": r0,
        "R1": r1,
        "R2": r2,
        "R3": r3,
        "RQ": rq,
    }

def case_checks(rows, cases):
    check(len(cases) == 37, "Observation cohort changed")
    check(len(rows) == 37, "Unexpected observation count")
    ids = [r["case_id"] for r in rows]
    check(len(set(ids)) == 37, "Repeated case IDs")
    check(len({r["source_profile"] for r in rows}) == 6, "Source-profile count changed")
    actual_profiles = {profile: sum(r["source_profile"] == profile for r in rows)
                       for profile in EXPECTED_PROFILES}
    check(actual_profiles == EXPECTED_PROFILES, "Source-profile distribution changed")
    check(sum(r["RQ"] for r in rows) == 9, "Source-qualified cohort changed")
    for r in rows:
        check(not r["R1"] or r["R0"], "R1 must imply R0")
        check(not r["R2"] or r["R1"], "R2 must imply R1")
        check(not r["R3"] or r["R2"], "R3 must imply R2")
        check(not r["RQ"] or r["R3"], "Source licensed case excluded by R3: " + r["case_id"])
    # Contrasts target precisely the metadata the generic projection discards.
    mapping = {c["id"]: c for c in cases}
    d = copy.deepcopy(mapping["DRV-001"])
    d["response"]["incompleteSearch"] = True
    check(project(d) == project(mapping["DRV-001"]), "Drive completeness-leakage control")
    e = copy.deepcopy(mapping["ES-001"])
    e["response"]["timed_out"] = True
    check(project(e) == project(mapping["ES-001"]), "Elasticsearch timeout-leakage control")
    m = copy.deepcopy(mapping["MSG-001"])
    m["response"]["pages"][-1]["response"]["@odata.deltaLink"] = ""
    check(project(m) == project(mapping["MSG-001"]), "Graph completion-leakage control")
    wrong_count = copy.deepcopy(mapping["ES-001"])
    wrong_count["response"]["hits"]["total"]["value"] = 2
    check(project(wrong_count)["reported_zero"] is False, "Count-positive sensitivity")
    visible_hit = copy.deepcopy(mapping["DRV-001"])
    visible_hit["response"]["files"] = [{"id": "control-hit"}]
    check(project(visible_hit)["empty_visible"] is False, "Result-positive sensitivity")
    return actual_profiles

def aggregate(rows):
    table = {}
    for rule in ("R0", "R1", "R2", "R3", "RQ"):
        committed = [r for r in rows if r[rule]]
        licensed = sum(r["RQ"] for r in committed)
        table[rule] = {
            "commits": len(committed),
            "licensed": licensed,
            "unlicensed": len(committed) - licensed,
        }
        check(tuple(table[rule].values()) == EXPECTED_COUNTS[rule],
              f"Manuscript Table II mismatch at {rule}: {table[rule]}")
    return table

def get_outputs():
    data = inspect_bytes()
    check(data["corpusVersion"] == "closureprobe-corpus-v0.3.0", "Corpus version changed")
    check(data["profileVersion"] == "0.3.0", "Producer profile version changed")
    all_cases = data["cases"]
    check(len(all_cases) == 50, "Total corpus count changed")
    observations = [c for c in all_cases if c.get("kind") == "observation"]
    traces = [c for c in all_cases if c.get("kind") == "trace"]
    check(len(traces) == 13, "Trace exclusion changed")
    rows = sorted((row(c) for c in observations), key=lambda x: x["case_id"])
    case_checks(rows, observations)
    table = aggregate(rows)

    profiles = {}
    for profile in EXPECTED_PROFILES:
        subset = [r for r in rows if r["source_profile"] == profile]
        profiles[profile] = {
            "observations": len(subset),
            "source_licensed": sum(r["RQ"] for r in subset),
            "R3_commits": sum(r["R3"] for r in subset),
            "R3_unlicensed_case_ids": sorted(
                r["case_id"] for r in subset if r["R3"] and not r["RQ"]
            ),
        }
    metadata = {
        "source": {
            "repository": "https://github.com/risu-research/closureprobe",
            "commit": SOURCE_COMMIT,
            "path": "corpus/v0.3/cases.json",
            "corpus_version": data["corpusVersion"],
            "sha256": SOURCE_SHA256,
            "git_blob_sha1": SOURCE_GIT_BLOB,
        },
        "cohort": {
            "total_source_cases": 50,
            "observations": 37,
            "excluded_cross_boundary_traces": 13,
            "source_licensed": 9,
        },
        "rules": {
            "R0": "empty returned container",
            "R1": "R0 plus execution success",
            "R2": "R1 plus initial request and final segment",
            "R3": "R2 plus observed zero",
            "RQ": "source-qualified label frozen with the original corpus",
        },
        "table_ii": table,
        "profiles": profiles,
    }
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: (str(r[k]).lower() if isinstance(r[k], bool) else r[k]) for k in FIELDS})
    files = {
        "rows.csv": buf.getvalue(),
        "table_ii.json": json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    }
    return metadata, files

def main():
    parser = argparse.ArgumentParser(description="Recompute the 37-case exploratory Table II")
    parser.add_argument("--write", metavar="DIRECTORY", help="Write row-level reproducible outputs")
    parser.add_argument("--verify", metavar="DIRECTORY", help="Compare regenerated outputs byte-for-byte")
    options = parser.parse_args()
    check(not (options.write and options.verify), "Select one output mode")
    report, outputs = get_outputs()
    if options.write:
        path = Path(options.write)
        path.mkdir(parents=True, exist_ok=True)
        for name, value in outputs.items():
            (path / name).write_text(value, encoding="utf-8", newline="")
    if options.verify:
        path = Path(options.verify)
        for name, value in outputs.items():
            check((path / name).read_bytes() == value.encode("utf-8"),
                  "Archived row or table mismatch: " + name)
    print(json.dumps({"PASS": True, "cases": 37, "source_licensed": 9,
                      "table_ii": report["table_ii"],
                      "metamorphic_controls": 5,
                      "source_sha256": SOURCE_SHA256}, sort_keys=True))

if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, FileNotFoundError) as error:
        print("DISCOVERY37_REPLAY_FAILED:", error, file=sys.stderr)
        sys.exit(1)
