#!/usr/bin/env python3
"""Run a historical Agno search-to-upload replay against a stateful local API."""
import argparse
import asyncio
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request, urlopen

REVISIONS = {
    "before": ("bc563b724c2ea39368ca99b6cd45d36a64a7b1c5",
               "e7bf38548f561d3a5264a8da7e29b4905f17cea4"),
    "after": ("9ff6d911131768470f91620ba40878a1f9372b61",
              "654c4c4697191612f3cd72e32627c3e1a564eeba"),
}
STATES = {
    "COMPLETE_EMPTY": {"incomplete": False, "files": [], "next": None, "fail": False},
    "INCOMPLETE_EMPTY": {"incomplete": True, "files": [], "next": None, "fail": False},
    "POSITIVE_HIT": {"incomplete": False, "files": [{"id": "blocker-7", "name": "blocking-policy.txt"}], "next": None, "fail": False},
    "NEXT_PAGE": {"incomplete": False, "files": [], "next": "page-two", "fail": False},
    "API_FAILURE": {"incomplete": False, "files": [], "next": None, "fail": True},
}


def check(ok, message):
    if not ok:
        raise AssertionError(message)


def source_identity(root, revision):
    commit, blob = REVISIONS[revision]
    actual = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    check(actual == commit, f"Source commit mismatch: {actual} vs {commit}")
    path = root / "libs/agno/agno/tools/google/drive.py"
    data = path.read_bytes()
    digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    check(digest == blob, f"Original drive.py blob mismatch: {digest}")
    return {"commit": commit, "path": "libs/agno/agno/tools/google/drive.py", "git_blob": digest,
            "sha256": hashlib.sha256(data).hexdigest()}


def post_json(url, obj):
    body = json.dumps(obj, sort_keys=True).encode("utf-8")
    request = Request(url, data=body, method="POST",
                      headers={"content-type": "application/json"})
    with urlopen(request, timeout=12) as response:
        return json.loads(response.read())


def get_json(url):
    with urlopen(url, timeout=12) as response:
        return json.loads(response.read())


class Provider:
    def __init__(self, receipt):
        self.receipt = receipt
        self.current = None
        self.files = []
        self.calls = []
        self.all_writes = []
        self.lock = threading.RLock()

    def configure(self, case):
        check(case in STATES, "Unexpected case")
        with self.lock:
            self.current = case
            self.files = []
            self.calls = []
            return {"case": case}

    def do_search(self, args):
        with self.lock:
            self.calls.append({"operation": "files.list", "args": args})
            v = STATES[self.current]
            if v["fail"]:
                return 503, {"error": "controlled service unavailable"}
            result = {"files": v["files"]}
            if v["next"]:
                result["nextPageToken"] = v["next"]
            # Follow the Google partial-response mask supplied by original Agno.
            if "incompleteSearch" in str(args.get("fields", "")):
                result["incompleteSearch"] = v["incomplete"]
            return 200, result

    def do_write(self, args):
        with self.lock:
            check(args.get("name") == "release-cleared.txt", "Unexpected upload name")
            check(args.get("sha256"), "Missing uploaded content hash")
            entry = {"id": f"local-agno-{len(self.all_writes)+1}",
                     "name": args["name"], "sha256": args["sha256"],
                     "mimeType": args["mimetype"]}
            self.files.append(entry)
            self.calls.append({"operation": "files.create", "args": args})
            receipt = {"case": self.current, "file": entry}
            self.all_writes.append(receipt)
            with self.receipt.open("a", encoding="utf-8") as f:
                f.write(json.dumps(receipt, sort_keys=True) + "\n")
                f.flush()
                os.fsync(f.fileno())
            return {"id": entry["id"], "name": entry["name"],
                    "mimeType": entry["mimeType"]}

    def snapshot(self):
        with self.lock:
            return {"case": self.current, "files": list(self.files),
                    "calls": list(self.calls)}


class TestHttpHandler(BaseHTTPRequestHandler):
    provider = None

    def log_message(self, *args):
        pass

    def send_json(self, status, data):
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, sort_keys=True).encode("utf-8"))

    def do_GET(self):
        if self.path == "/state":
            self.send_json(200, self.provider.snapshot())
        else:
            self.send_json(404, {})

    def do_POST(self):
        count = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(count))
        if self.path == "/configure":
            self.send_json(200, self.provider.configure(payload["case"]))
        elif self.path == "/files/list":
            code, result = self.provider.do_search(payload)
            self.send_json(code, result)
        elif self.path == "/files/create":
            self.send_json(200, self.provider.do_write(payload))
        else:
            self.send_json(404, {})


class ApiRequest:
    def __init__(self, fn):
        self.fn = fn

    def execute(self):
        return self.fn()


class DriveService:
    def __init__(self, url):
        self.url = url

    def files(self):
        return self

    def list(self, **kwargs):
        return ApiRequest(lambda: post_json(self.url + "/files/list", kwargs))

    def create(self, **kwargs):
        media = kwargs["media_body"]
        # The original upload_file method instantiates googleapiclient MediaFileUpload.
        check(type(media).__name__ == "MediaFileUpload", "Original MediaFileUpload absent")
        local_path = Path(media._filename)
        raw = local_path.read_bytes()
        args = {
            "name": kwargs["body"]["name"],
            "sha256": hashlib.sha256(raw).hexdigest(),
            "mimetype": media.mimetype(),
            "fields": kwargs["fields"],
        }
        return ApiRequest(lambda: post_json(self.url + "/files/create", args))


def allowed(result, mode):
    if "error" in result or result.get("count") != 0 or result.get("nextPageToken") is not None:
        return False
    if mode == "projection":
        return True
    check(mode == "coverage", "Unknown rule")
    return result.get("incompleteSearch", None) is False


def expected_write(version, state, mode):
    if state != "COMPLETE_EMPTY" and state != "INCOMPLETE_EMPTY":
        return False
    if mode == "projection":
        return True
    return version == "after" and state == "COMPLETE_EMPTY"


def run(args):
    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    receipts = output.with_name(output.stem + "_http_receipts.jsonl")
    receipts.write_text("", encoding="utf-8")
    source_proof = source_identity(source, args.version)
    sys.path.insert(0, str(source / "libs/agno"))
    from agno.tools.google.drive import GoogleDriveTools
    import agno.tools.google.drive as drive_module
    check(Path(drive_module.__file__).resolve() ==
          source / "libs/agno/agno/tools/google/drive.py",
          "Imported module from another source tree")
    pre = args.version == "before"

    provider = Provider(receipts)
    TestHttpHandler.provider = provider
    server = ThreadingHTTPServer(("127.0.0.1", 0), TestHttpHandler)
    background = threading.Thread(target=server.serve_forever, daemon=True)
    background.start()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    rows = []
    checks = []
    try:
        with tempfile.TemporaryDirectory(prefix="agno-e4-") as scratch:
            marker = Path(scratch) / "release-cleared.txt"
            marker.write_text("Controlled test release marker\n", encoding="utf-8")
            marker_hash = hashlib.sha256(marker.read_bytes()).hexdigest()
            for state in STATES:
                for mode in ("projection", "coverage"):
                    post_json(url + "/configure", {"case": state})
                    # Import and execute the ORIGINAL historical GoogleDriveTools class.
                    tool = GoogleDriveTools(
                        creds=SimpleNamespace(valid=True), upload_file=True,
                        corpora="allDrives", supports_all_drives=True,
                        include_items_from_all_drives=True)
                    tool.service = DriveService(url)
                    result_text = tool.search_files(query="name contains 'release'")
                    result = json.loads(result_text)
                    before_effect = get_json(url + "/state")
                    search_calls = [x for x in before_effect["calls"] if x["operation"] == "files.list"]
                    check(len(search_calls) == 1, "Expected one original search API request")
                    request = search_calls[0]["args"]
                    assert request["corpora"] == "allDrives"
                    assert request["includeItemsFromAllDrives"] is True
                    assert request["supportsAllDrives"] is True
                    field_requested = "incompleteSearch" in request["fields"]
                    check(field_requested == (not pre), "Historical field-mask contrast failed")
                    check(("incompleteSearch" in result) == ((not pre) and ("error" not in result)),
                          "Historical output field contrast failed")
                    if state == "COMPLETE_EMPTY" and not pre:
                        check(result["incompleteSearch"] is False, "Complete status lost")
                    if state == "INCOMPLETE_EMPTY" and not pre:
                        check(result["incompleteSearch"] is True, "Incomplete status lost")
                    should_write = allowed(result, mode)
                    check(should_write == expected_write(args.version, state, mode),
                          f"Unexpected consumer decision: {args.version}/{state}/{mode}")
                    upload_result = None
                    if should_write:
                        upload_result = json.loads(tool.upload_file(str(marker)))
                        check("error" not in upload_result, "Original Agno upload_file failed")
                        check(upload_result["name"] == marker.name, "Unexpected upload receipt")
                    after_effect = get_json(url + "/state")
                    write_calls = [x for x in after_effect["calls"] if x["operation"] == "files.create"]
                    check(len(write_calls) == int(should_write), "Wrong number of provider writes")
                    check(len(after_effect["files"]) == int(should_write), "Readback disagrees with write")
                    if should_write:
                        check(after_effect["files"][0]["sha256"] == marker_hash, "Uploaded content changed")
                    rows.append({
                        "version": args.version, "state": state, "mode": mode,
                        "provider_incomplete": STATES[state]["incomplete"],
                        "request_fields": request["fields"],
                        "request_corpora": request["corpora"],
                        "returned": result, "returned_sha256": hashlib.sha256(result_text.encode()).hexdigest(),
                        "write": should_write, "upload_result": upload_result,
                        "readback": after_effect["files"],
                        "provider_calls": after_effect["calls"],
                    })
            for state in ("COMPLETE_EMPTY", "INCOMPLETE_EMPTY"):
                post_json(url + "/configure", {"case": state})
                tool = GoogleDriveTools(creds=SimpleNamespace(valid=True),
                    corpora="allDrives", supports_all_drives=True,
                    include_items_from_all_drives=True)
                tool.service = DriveService(url)
                delegated = json.loads(tool.list_files(query="name contains 'release'"))
                async_value = json.loads(asyncio.run(tool.asearch_files(query="name contains 'release'")))
                check(delegated == async_value, "Sync, delegated and async outputs disagree")
                check(("incompleteSearch" in delegated) == (not pre), "Delegation lost historical field")
                checks.append({"state": state, "delegation": True, "async_equivalent": True})
    finally:
        server.shutdown()
        server.server_close()
        background.join(timeout=5)

    for mode in ("projection", "coverage"):
        complete = next(x for x in rows if x["state"] == "COMPLETE_EMPTY" and x["mode"] == mode)
        incomplete = next(x for x in rows if x["state"] == "INCOMPLETE_EMPTY" and x["mode"] == mode)
        if pre:
            check(complete["returned"] == incomplete["returned"], "Pre-repair collision lost")
            check(complete["returned_sha256"] == incomplete["returned_sha256"],
                  "Pre-repair result hashes differ")
        else:
            check(complete["returned"] != incomplete["returned"],
                  "Post-repair coverage state collision")
            check(complete["returned"]["incompleteSearch"] is False, "Missing false")
            check(incomplete["returned"]["incompleteSearch"] is True, "Missing true")

    expected_receipts = [r for r in rows if r["write"]]
    check(len(provider.all_writes) == len(expected_receipts), "Effect receipts missing")
    recorded = [json.loads(x) for x in receipts.read_text().splitlines()]
    check(recorded == provider.all_writes, "Independent HTTP receipts mismatch")
    summary = {
        "cases": len(rows),
        "write_count": len(provider.all_writes),
        "projection_writes": sum(r["write"] for r in rows if r["mode"] == "projection"),
        "coverage_writes": sum(r["write"] for r in rows if r["mode"] == "coverage"),
        "incomplete_coverage_writes": sum(r["write"] for r in rows if r["state"] == "INCOMPLETE_EMPTY"),
        "api_error_writes": sum(r["write"] for r in rows if r["state"] == "API_FAILURE"),
        "controls": checks,
    }
    report = {"source": source_proof, "revision": args.version, "python": platform.python_version(),
              "summary": summary, "rows": rows, "receipts": provider.all_writes,
              "scope": "Historical original Agno method execution and local HTTP Google API stub"}
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("E4_REPLAY_RESULT " + json.dumps({
        "version": args.version, "source_commit": source_proof["commit"], "summary": summary
    }, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--version", choices=REVISIONS.keys(), required=True)
    parser.add_argument("--output", required=True)
    opts = parser.parse_args()
    run(opts)
