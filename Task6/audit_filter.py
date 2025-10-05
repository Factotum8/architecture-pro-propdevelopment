#!/usr/bin/env python3
"""
audit_filter.py

Filters Kubernetes audit log (JSON lines or newline-separated JSON objects).

Implements equivalents of:
  jq 'select(.objectRef.resource=="secrets" and .verb=="get")' audit.log
  jq 'select(.verb=="create" and .objectRef.subresource=="exec")' audit.log
  jq 'select(.objectRef.resource=="pods" and .requestObject.spec.containers[].securityContext.privileged==true)' audit.log
  grep -i 'audit-policy' audit.log
"""

import argparse
import json
import sys
from typing import Any, Dict, Iterator, Optional


def safe_get(obj: Dict[str, Any], *keys):
    """Safely traverse nested dicts/lists. Returns None if any step missing."""
    cur = obj
    for k in keys:
        if cur is None:
            return None
        # allow numeric index if current is list and key is int
        if isinstance(cur, list):
            try:
                idx = int(k)
            except Exception:
                return None
            if 0 <= idx < len(cur):
                cur = cur[idx]
            else:
                return None
        elif isinstance(cur, dict):
            cur = cur.get(k)
        else:
            return None
    return cur


def iter_json_objects(fileobj) -> Iterator[Dict[str, Any]]:
    """Yield JSON objects from a file. Accepts JSON-lines (one JSON per line) or
    a file containing a JSON array or multiple JSON objects separated by newlines."""
    first = True
    for raw in fileobj:
        line = raw.strip()
        if not line:
            continue
        # try parse line as JSON object (common case)
        try:
            obj = json.loads(line)
            yield obj
            continue
        except Exception:
            pass
        # if here, maybe the file is a single JSON array or pretty JSON: try to load whole file once
        if first:
            # read rest of file including current line
            rest = raw + fileobj.read()
            first = False
            try:
                whole = json.loads(rest)
                if isinstance(whole, list):
                    for item in whole:
                        yield item
                elif isinstance(whole, dict):
                    yield whole
                else:
                    # unknown JSON top-level
                    pass
                return
            except Exception:
                # give up for this chunk; continue trying line-by-line next iterations
                continue
        else:
            continue


def filter_secrets_get(obj: Dict[str, Any]) -> bool:
    return safe_get(obj, "objectRef", "resource") == "secrets" and safe_get(obj, "verb") == "get"


def filter_create_exec(obj: Dict[str, Any]) -> bool:
    return safe_get(obj, "verb") == "create" and safe_get(obj, "objectRef", "subresource") == "exec"


def filter_privileged_pods(obj: Dict[str, Any]) -> bool:
    # objectRef.resource == "pods" AND any container.securityContext.privileged == true
    if safe_get(obj, "objectRef", "resource") != "pods":
        return False
    # requestObject may be absent; handle safely
    req = safe_get(obj, "requestObject")
    if not isinstance(req, dict):
        return False
    spec = req.get("spec")
    if not isinstance(spec, dict):
        return False
    containers = spec.get("containers") or []
    for c in containers:
        sc = c.get("securityContext") if isinstance(c, dict) else None
        if isinstance(sc, dict) and sc.get("privileged") is True:
            return True
    return False


def grep_text(line: str, term: str) -> bool:
    return term.lower() in line.lower()


def main():
    p = argparse.ArgumentParser(description="Filter Kubernetes audit logs like jq/grep examples.")
    p.add_argument("file", help="Path to audit log (JSON-lines or JSON array)")
    p.add_argument("--secrets-get", action="store_true", help='select .objectRef.resource=="secrets" and .verb=="get"')
    p.add_argument("--create-exec", action="store_true", help='select .verb=="create" and .objectRef.subresource=="exec"')
    p.add_argument("--privileged-pods", action="store_true", help='select pods with containers[].securityContext.privileged==true')
    p.add_argument("--grep", metavar="TERM", help="Case-insensitive text search in raw lines (like grep -i TERM)")
    p.add_argument("--pretty", action="store_true", help="Pretty-print matching JSON objects")
    p.add_argument("--raw", action="store_true", help="Print original raw lines where applicable (for grep)")
    args = p.parse_args()

    filters = []
    if args.secrets_get:
        filters.append(("secrets-get", filter_secrets_get))
    if args.create_exec:
        filters.append(("create-exec", filter_create_exec))
    if args.privileged_pods:
        filters.append(("privileged-pods", filter_privileged_pods))
    # note: argparse variable names normalized: create-exec -> args.create_exec, privileged-pods -> args.privileged_pods
    # adapt:
    if args.create_exec and ("create-exec", filter_create_exec) not in filters:
        filters.append(("create-exec", filter_create_exec))
    if args.privileged_pods and ("privileged-pods", filter_privileged_pods) not in filters:
        filters.append(("privileged-pods", filter_privileged_pods))

    # If no filters specified, show help
    if not (filters or args.grep):
        p.print_help()
        sys.exit(1)

    term = args.grep.lower() if args.grep else None

    with open(args.file, "r", encoding="utf-8") as fh:
        # For grep we may want raw lines; but we still attempt to parse JSON per line
        for raw in fh:
            line = raw.rstrip("\n")
            matched = False

            # grep check first (works on raw line)
            if term and grep_text(line, term):
                matched = True
                if args.raw:
                    print(line)
                    continue
                # else fall through to JSON parsing to pretty-print if requested

            # try parse JSON
            obj = None
            try:
                obj = json.loads(line)
            except Exception:
                # not a JSON line; if grep already matched, printed above when --raw
                continue

            # run filters (if any). If multiple filters requested, print if any match (OR semantics).
            if filters:
                for name, f in filters:
                    try:
                        if f(obj):
                            matched = True
                            break
                    except Exception:
                        # ignore filter errors on malformed objects
                        continue

            if matched:
                if args.pretty:
                    print(json.dumps(obj, indent=2, ensure_ascii=False))
                else:
                    # print compact JSON
                    print(json.dumps(obj, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
