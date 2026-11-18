#!/usr/bin/env python3
"""List what to fix in a GEDCOM export, without a vault.

Reads one .gedcom file and reports duplicate events and families, marriages
recorded on a person, unreadable or non-standard dates, and place spellings
that disagree. Each finding names the person, the line in the file and a fix
to make in the tree's host (Ancestry, MyHeritage, ...). The file is never
written.

    python3 <lib>/gedcom_check.py                      FamilyTree.ged, all checks
    python3 <lib>/gedcom_check.py --ged FILE           another file
    python3 <lib>/gedcom_check.py --only dates,places  some groups only
    python3 <lib>/gedcom_check.py --json               machine-readable, no limit
    python3 <lib>/gedcom_check.py --out FILE           also write the report to FILE

Exit codes: 0 no findings; 1 findings; 2 the run could not start (bad flags,
missing or unreadable GEDCOM).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict

from crsync import gedcheck, gedcom, report

DEFAULT_GED = "FamilyTree.ged"
DEFAULT_LIMIT = 20


def _header(path: str, tree, host: str) -> list[str]:
    lines = [f"GEDCOM:   {path}",
             f"Size:     {os.path.getsize(path):,} bytes",
             f"SHA-256:  {report.sha256(path)}",
             f"Host:     {host}",
             f"Exported: {tree.header.get('date') or '(no date in HEAD)'}"]
    lines += [f"WARNING {w}" for w in tree.warnings]
    return lines


def _summary(findings: list) -> list[str]:
    lines = []
    for group in gedcheck.GROUPS:
        rows = []
        for check, grp in gedcheck.CHECKS.items():
            if grp != group:
                continue
            hits = [f for f in findings if f.check == check]
            if hits:
                fixes = sum(f.kind == "fix" for f in hits)
                rows.append(f"  {check:<20} {len(hits):>4}  "
                            f"({fixes} fix, {len(hits) - fixes} review)")
        if rows:
            lines += [f"{group}:"] + rows
    fixes = sum(f.kind == "fix" for f in findings)
    lines.append(f"{len(findings)} findings ({fixes} fix, "
                 f"{len(findings) - fixes} review)")
    return lines


def _details(findings: list, limit: int) -> list[str]:
    lines = []
    for check in gedcheck.CHECKS:
        hits = [f for f in findings if f.check == check]
        if not hits:
            continue
        lines += ["", f"== {check} ({len(hits)}) =="]
        shown = hits if limit <= 0 else hits[:limit]
        for f in shown:
            lines += [f"{f.who}  line {f.line}", f"  {f.what}", f"  {f.fix}"]
        if len(shown) < len(hits):
            lines.append(f"  ... and {len(hits) - len(shown)} more "
                         f"(--limit 0 shows all)")
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="List what to fix in a GEDCOM export; never writes it.")
    ap.add_argument("--ged", default=DEFAULT_GED,
                    help=f"GEDCOM file (default {DEFAULT_GED})")
    ap.add_argument("--only", default="",
                    help="comma-separated groups: "
                         + ", ".join(gedcheck.GROUPS))
    ap.add_argument("--json", action="store_true",
                    help="print JSON (all findings; ignores --limit)")
    ap.add_argument("--out", metavar="FILE",
                    help="also write the report to FILE")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                    help="findings shown per check in text (default "
                         f"{DEFAULT_LIMIT}; 0 shows all)")
    args = ap.parse_args(argv)

    try:
        only = gedcheck.parse_only(args.only)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    if not os.path.isfile(args.ged):
        print(f"No GEDCOM at {args.ged}", file=sys.stderr)
        return 2
    try:
        tree = gedcom.parse(args.ged, warn=lambda m: None)
        digest = report.sha256(args.ged)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"GEDCOM unreadable: {exc}", file=sys.stderr)
        return 2

    host = gedcheck.host_name(tree)
    findings = gedcheck.run(tree, only)
    if args.json:
        text = json.dumps(
            {"ged": args.ged, "host": host,
             "exported": tree.header.get("date") or "",
             "sha256": digest, "warnings": list(tree.warnings),
             "findings": [asdict(f) for f in findings]},
            ensure_ascii=False, indent=2)
    else:
        lines = _header(args.ged, tree, host) + [""]
        lines += _summary(findings) if findings else ["No findings."]
        lines += _details(findings, args.limit)
        text = "\n".join(lines)
    print(text)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        except OSError as exc:
            print(f"Cannot write {args.out}: {exc}", file=sys.stderr)
            return 2
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
