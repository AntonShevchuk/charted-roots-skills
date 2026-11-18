#!/usr/bin/env python3
"""Vault invariants for the Charted Roots vault.

Reads no GEDCOM and writes nothing, so it runs as a baseline before and after
any edit -- a sync, a merge, a new archive record.

    python3 <lib>/vault_verify.py
    python3 <lib>/vault_verify.py --limit 50

Exit codes: 0 every check passed; 1 a check failed; 2 the run could not start
(unreadable vault or plugin settings).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from crsync import config, verify


def cmd_verify(cfg: config.Config, limit: int) -> int:
    idx = verify.Index(cfg)
    print(f"Vault: {cfg.root}")
    print(f"Indexed {len(idx.notes)} notes, {idx.attachment_count} attachments\n")
    print("Invariants")
    results = verify.run(cfg, idx)
    for r in results:
        print(r.render(limit=limit))
    failed = [r for r in results if not r.ok]
    print()
    if failed:
        print(f"{len(failed)} of {len(results)} checks FAILED")
    else:
        print(f"all {len(results)} checks passed")
    return 1 if failed else 0


def load_config(root: str) -> config.Config | None:
    """The plugin settings under `root`, or None after printing why not."""
    # A mistyped --vault would otherwise index an empty tree and pass every
    # invariant.
    if not os.path.isdir(root):
        print(f"No vault at {root}", file=sys.stderr)
        return None
    try:
        return config.load(root)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"Plugin settings unreadable: {exc}", file=sys.stderr)
        return None


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vault_verify.py",
        description="Check the vault's invariants. Reads no GEDCOM, writes nothing.",
    )
    p.add_argument("--vault", default=".", help="vault root (default: cwd)")
    p.add_argument("--limit", type=int, default=10, help="max detail lines per finding")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    cfg = load_config(args.vault)
    if cfg is None:
        return 2
    return cmd_verify(cfg, args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
