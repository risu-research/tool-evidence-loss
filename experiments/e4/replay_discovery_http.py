#!/usr/bin/env python3
"""Run pinned original Agno search against the installed Google Discovery client."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from replay_agno import REVISIONS, source_identity

class MockWireHttp:
    def __init__(self, incomplete):
        self.incomplete = incomplete
        self.calls = []

    def request(self, uri, method="GET", body=None, headers=None, **kwargs):
        from httplib2 import Response
        parsed = urlparse(uri)
        query = parse_qs(parsed.query)
        self.calls.append({
            "path": parsed.path,
            "method": method,
            "fields": query.get("fields", [None])[0],
            "corpora": query.get("corpora", [None])[0],
            "supportsAllDrives": query.get("supportsAllDrives", [None])[0],
            "includeItemsFromAllDrives": query.get("includeItemsFromAllDrives", [None])[0],
        })
        if parsed.path != "/drive/v3/files":
            raise AssertionError(f"Unexpected Google service path: {parsed.path}")
        data = {"kind": "drive#fileList", "files": [], "incompleteSearch": self.incomplete}
        return Response({"status": "200", "content-type": "application/json"}), json.dumps(data).encode()


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--version", choices=REVISIONS.keys(), required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--output", required=True)
    args=p.parse_args()
    root=Path(args.source).resolve()
    source=source_identity(root,args.version)
    sys.path.insert(0,str(root/"libs/agno"))
    from agno.tools.google.drive import GoogleDriveTools
    import agno.tools.google.drive as module
    from googleapiclient.discovery import build
    from types import SimpleNamespace

    assert Path(module.__file__).resolve() == root/"libs/agno/agno/tools/google/drive.py"
    rows=[]
    for incomplete in (False,True):
        fake=MockWireHttp(incomplete)
        actual_client=build("drive","v3",http=fake,static_discovery=True)
        tool=GoogleDriveTools(creds=SimpleNamespace(valid=True),
            corpora="allDrives",supports_all_drives=True,include_items_from_all_drives=True)
        tool.service=actual_client
        result=json.loads(tool.search_files(query="name contains 'release'"))
        assert len(fake.calls)==1
        call=fake.calls[0]
        assert call["method"]=="GET"
        assert call["corpora"]=="allDrives"
        expected_present=args.version=="after"
        assert ("incompleteSearch" in call["fields"]) is expected_present
        assert ("incompleteSearch" in result) is expected_present
        if expected_present:
            assert result["incompleteSearch"] is incomplete
        rows.append({"provider_incomplete":incomplete,"request":call,"tool_result":result})
    if args.version=="before":
        assert rows[0]["tool_result"]==rows[1]["tool_result"]
    else:
        assert rows[0]["tool_result"]!=rows[1]["tool_result"]
    report={
        "pass":True,
        "source":source,
        "revision":args.version,
        "transport":"real googleapiclient Discovery v3; mocked HTTP responses",
        "states":rows
    }
    Path(args.output).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("E4_DISCOVERY_HTTP_PASS "+json.dumps({"source_commit":source["commit"],
        "version":args.version,"requests":len(rows),"field_visible":args.version=="after"},sort_keys=True))

if __name__=="__main__":
    main()
