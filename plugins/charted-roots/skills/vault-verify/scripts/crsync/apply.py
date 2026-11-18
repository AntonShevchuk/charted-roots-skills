"""Execute a plan.

Only the changes that cannot lose information are written:

* `fill`   -- the vault field is empty and the GEDCOM has a value
* `refine` -- the GEDCOM value is strictly more precise
* `format` -- the same date, respelt into the form the plugin validates
  (`ABT 1804` -> `c. 1804`; see `crsync/dates.py`)

`case`, `coarsen` and `conflict` are reported and never applied. Ancestry
normalises the German nobiliary particle to `Von` and drops the `ABT`
qualifier and Russian patronymics; applying those would revert curated work,
which is the opposite of what this script is for.

Individual coarsen and conflict changes the user has reviewed and accepted
are named in `History/gedcom-sync-decisions.json` -- one ruling per person and
field, with its reason. See `crsync/decisions.py`.

Preconditions are hard failures, not warnings. The most important is that
Obsidian must be closed. Two reasons, and only the first is conditional: if
`enableBidirectionalSync` and `syncOnFileModify` are both on in `data.json`,
the plugin writes the reciprocal of every relationship on file modify and
would race this run; and whatever those settings say, Obsidian rewrites
`data.json` from memory when it exits and an open editor can write a note
back from its own buffer.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass

from . import decisions as decisions_mod
from . import events as events_mod
from . import match
from . import vault

#: Change classes `--apply` will always write.
SAFE = {match.FILL, match.REFINE, match.FORMAT}

#: Accept nothing. `coarsen` and `conflict` are held unless a ruling in
#: History/gedcom-sync-decisions.json names that person and that field --
#: see crsync/decisions.py.
NO_DECISIONS = decisions_mod.Decisions()


def _uppercase_count(text: str) -> int:
    return sum(1 for ch in text if ch.isupper())


def case_direction(plan, entity: str) -> int:
    """+1 if every case change adds capitals, -1 if every one removes them, 0 if mixed.

    A `case` difference is only safe to apply when the whole run agrees on
    which side is correct. Ancestry title-cases the German nobiliary particle
    (`von` -> `Von`), which would revert curated work; but once it is fixed
    upstream the same class runs the other way and the vault is the stale
    side. Direction, not the class, decides.
    """
    signs = set()
    for action in plan.of(entity, "update") + plan.of(entity, "adopt"):
        for change in action.changes:
            if change.kind != match.CASE:
                continue
            delta = _uppercase_count(match._as_text(change.new)) - \
                _uppercase_count(match._as_text(change.old))
            if delta:
                signs.add(1 if delta > 0 else -1)
    return signs.pop() if len(signs) == 1 else 0


def obsidian_running() -> bool | None:
    """True if Obsidian is running, False if not, None if it cannot be told.

    The CLI had a second copy of this that returned False when `pgrep` could
    not be run, which reads as "Obsidian is closed" -- the same fail-open
    shape as a `git status` that fails and reads as a clean tree. An
    unanswerable question gets None, and the precondition blocks on it.

    pgrep exits 0 for a match and 1 for none; anything else is pgrep itself
    failing, not an answer about Obsidian.
    """
    try:
        done = subprocess.run(["pgrep", "-x", "Obsidian"], capture_output=True)
    except OSError:
        return None
    if done.returncode in (0, 1):
        return done.returncode == 0
    return None


def sync_state(cfg) -> str:
    """Whether the plugin's reciprocal sync is live: "on" or "off"."""
    return "on" if cfg.bidirectional_sync else "off"


def sync_flags(cfg) -> str:
    """The two settings that decide it, as `data.json` has them."""
    return ", ".join(f"{key} {'on' if cfg.settings.get(key) else 'off'}"
                     for key in ("enableBidirectionalSync", "syncOnFileModify"))


def sync_remedy(cfg) -> str:
    """Why to close Obsidian, asserted from the settings rather than stated.

    The vault model: name the setting, then the rule that follows if it is on. This
    text used to declare bidirectional sync ON as a fact about the vault,
    which is false for any vault that turns it off -- and an argument from a
    setting nobody read is one the reader cannot act on. Either way there is
    a reason to quit; only the first half is conditional.
    """
    if cfg.bidirectional_sync:
        return ("Quit Obsidian. enableBidirectionalSync and syncOnFileModify "
                "are both on in data.json, so the plugin would write the "
                "reciprocal of every relationship this run writes and race "
                "it -- and it rewrites data.json from memory on exit.")
    return (f"Quit Obsidian. Bidirectional sync is not live ({sync_flags(cfg)}), "
            "so nothing would reciprocate these writes; but Obsidian still "
            "rewrites data.json from memory on exit, and an open editor can "
            "write a note back from its own buffer.")


@dataclass
class Precondition:
    name: str
    ok: bool
    detail: str = ""
    remedy: str = ""


def _git(root: str, *args) -> tuple:
    """Run git under `root`. Returns (ok, stdout); ok is False if git failed.

    An empty `git status` means a clean tree; an empty one because `root` is
    not a repository, or git is not installed, means nothing at all. The two
    are indistinguishable from stdout alone, and reading the second as the
    first is how a guarded write happens on an unguarded vault.
    """
    try:
        out = subprocess.run(["git", "-C", root, *args],
                             capture_output=True, text=True)
    except OSError as exc:
        return False, str(exc)
    return out.returncode == 0, out.stdout.strip()


#: Name of the clean-tree precondition.
CLEAN = "entity folders are clean in git"


def check_preconditions(cfg, require_restore_point: bool = True,
                        allow_obsidian: bool = False,
                        allow_dirty: bool = False) -> list:
    checks = []

    running = obsidian_running()
    remedy = sync_remedy(cfg)
    if running is None:
        state = "cannot tell: pgrep could not be run"
        remedy = ("This could not be checked -- `pgrep -x Obsidian` did not "
                  "answer. Pass --allow-obsidian-open only if you know it is "
                  "closed. " + remedy)
    else:
        state = "Obsidian is running" if running else "not running"
    checks.append(Precondition(
        "Obsidian is closed", running is False or allow_obsidian,
        f"{state} (bidirectional sync {sync_state(cfg)})", remedy))

    # The folders data.json names, not a fixed layout: a vault that keeps
    # People elsewhere must not be checked against a folder it never uses.
    ok, dirty = _git(cfg.root, "status", "--porcelain", "--", *cfg.entity_paths)
    if not ok:
        # Not overridable by --allow-dirty: that flag says "I have reviewed
        # the uncommitted changes", which nobody can have done here.
        checks.append(Precondition(
            CLEAN, False, f"git status failed: {dirty}",
            "This check could not be evaluated. Run the script from inside "
            "the vault's git repository; an unreadable tree is not a clean one."))
    else:
        checks.append(Precondition(
            CLEAN, (not dirty) or allow_dirty,
            f"{len(dirty.splitlines())} modified" if dirty else "clean",
            "Commit or stash the entity folders first, so this run's diff is "
            "reviewable on its own."))

    if require_restore_point:
        ok, head = _git(cfg.root, "rev-parse", "HEAD")
        ok_tags, tag_out = _git(cfg.root, "tag", "--points-at", head) if head \
            else (False, "")
        if not (ok and ok_tags):
            checks.append(Precondition(
                "a restore point tags HEAD", False, "git rev-parse/tag failed",
                "This check could not be evaluated -- no repository, or no "
                "commit to tag. Pass --no-restore-point only if you have "
                "another way back."))
        else:
            restore = [t for t in tag_out.splitlines()
                       if t.startswith("pre-gedcom-sync")]
            checks.append(Precondition(
                "a restore point tags HEAD", bool(restore),
                restore[0] if restore else "none",
                f"git tag pre-gedcom-sync-$(date +%Y%m%d-%H%M)  "
                f"# then re-run. The script never tags on your behalf."))
    return checks


def safe_changes(action, allow_case: bool = False, external_id: str = "",
                 decisions=None) -> list:
    """The changes on `action` that may be written, per policy and rulings."""
    decisions = decisions or NO_DECISIONS
    exempt = decisions.coarsen_exempt.get(external_id, set())
    accepted = decisions.conflict_accepted.get(external_id, set())
    out = []
    for c in action.changes:
        if c.kind in SAFE:
            out.append(c)
        elif c.kind == match.CASE and allow_case:
            out.append(c)
        elif c.kind == match.COARSEN and c.field in exempt:
            out.append(c)
        elif c.kind == match.CONFLICT and c.field in accepted:
            out.append(c)
    # A place change whose PLAC resolves to no Place note has nothing to
    # link, so no ruling can write it; it waits until the Place exists.
    return [c for c in out if c.field not in match.PERSON_PLACES
            or str(c.new).startswith("[[")]


def count_accepted(plan, entity: str, decisions) -> tuple:
    """(coarsen, conflict) changes in `plan` that the rulings let through.

    The dry run reports this: "N held changes are covered by the decisions
    file" is the only way to see, without writing, that a ruling still applies
    to the field it was made about. A reason left behind by an upstream fix
    shows up here as a ruling covering nothing.
    """
    n_coarsen = n_conflict = 0
    for action in plan.of(entity, "update") + plan.of(entity, "adopt"):
        exempt = decisions.coarsen_exempt.get(action.key, set())
        accepted = decisions.conflict_accepted.get(action.key, set())
        for change in action.changes:
            if change.kind == match.COARSEN and change.field in exempt:
                n_coarsen += 1
            elif change.kind == match.CONFLICT and change.field in accepted:
                n_conflict += 1
    return n_coarsen, n_conflict


def preflight(plan, entity: str, notes_by_path: dict, root: str,
              allow_case: bool = False, decisions=None) -> list:
    """(action, reason) for every planned change that could not be written.

    Two reasons, both a bug to look at rather than a note to skip. The target
    may not be in the index at all -- a planned write with nowhere to go is a
    matcher or indexing bug, and skipping it quietly means the run reports
    neither a write nor a hold and the next run plans it again. Or the note
    may be one the writer refuses: an unclosed frontmatter block, or a line
    the key index cannot see and a write could delete.

    Checked before anything is written, so the answer is "refuse" rather than
    "half-applied".
    """
    out = []
    for action in plan.of(entity, "update") + plan.of(entity, "adopt"):
        safe = safe_changes(action, allow_case=allow_case,
                            external_id=action.key, decisions=decisions)
        if not safe:
            continue
        note = notes_by_path.get(os.path.join(root, action.path))
        if note is None:
            out.append((action, "no note at that path in the index"))
        elif not note.writable:
            out.append((action, note.unwritable_reason()))
    return out


def apply_field_updates(plan, entity: str, notes_by_path: dict, root: str,
                        dry: bool = True, allow_case: bool = False,
                        decisions=None) -> tuple:
    """Write only the safe field changes.

    Returns (written, skipped, missing). `written` holds the notes that were
    actually rewritten -- a safe change whose value is already on disk is not
    one, so the count the caller prints is the count a `git diff` will show.
    `missing` is the actions whose note was not in the index, repeated from
    `preflight` so a caller that skipped that check still cannot lose them.
    """
    written, skipped, missing = [], [], []
    for action in plan.of(entity, "update") + plan.of(entity, "adopt"):
        safe = safe_changes(action, allow_case=allow_case,
                            external_id=action.key, decisions=decisions)
        held = [c for c in action.changes if c not in safe]
        if held:
            skipped.append((action, held))
        if not safe:
            continue
        note = notes_by_path.get(os.path.join(root, action.path))
        if note is None:
            missing.append((action, safe))
            continue
        for change in safe:
            if isinstance(change.new, list) and not change.new:
                # An emptied list means the key no longer applies; writing
                # `aliases:` with nothing under it is worse than no key.
                note.remove(change.field)
            else:
                note.set(change.field, change.new)
        if not note.dirty:
            continue
        if not dry:
            note.save()
        written.append((action, safe))
    return written, skipped, missing


def apply_event_updates(event_match, place_index, dry: bool = True) -> tuple:
    """Write the safe field changes on matched Events.

    Events are updated, never created or deleted here, and `sources`,
    `persons`, `title`, `confidence` and the body are never touched -- 671
    Events carry archive-derived `sources:` the export has never heard of,
    and a couple of hundred have hand-written bodies.
    """
    written, held = [], []
    for pair in event_match.pairs:
        changes = events_mod.event_changes(pair, place_index, match.Change)
        if not changes:
            continue
        safe = [c for c in changes if c.kind in SAFE]
        rest = [c for c in changes if c.kind not in SAFE]
        if rest:
            held.append((pair, rest))
        if not safe:
            continue
        note = pair.vault_note
        for change in safe:
            note.set(change.field, change.new)
        if not note.dirty:
            continue
        if not dry:
            note.save()
        written.append((pair, safe))
    return written, held


def write_event_keys(event_match, path: str, ged_sha: str, dry: bool = True) -> dict:
    """Persist the Event -> GEDCOM mapping as a sidecar keyed by cr_id.

    cr_id is the stable cross-note key and is independent of the filename, so
    the map survives a rename. Keeping it out of the Event notes preserves
    the vault model's "Events carry no import marker" invariant, which its own
    GEDCOM-reconciliation method depends on.
    """
    mapping = {}
    for pair in event_match.pairs:
        crid = pair.vault_note.scalar("cr_id")
        if crid:
            mapping[crid] = {"ged_key": pair.key, "stage": pair.stage}
    payload = {
        "_comment": "Event <-> GEDCOM mapping. Keyed by cr_id, which is "
                    "independent of the filename. Regenerable from the .ged.",
        "ged_sha256": ged_sha,
        "events": mapping,
    }
    if not dry:
        vault.write_atomic(path, json.dumps(
            payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    return mapping


def write_new_notes(creation_plan, dry: bool = True) -> list:
    """Write every planned new note. Order matters: Sources and People first,
    because Events and Citations link to them by filename."""
    written = []
    for group in (creation_plan.sources, creation_plan.people,
                  creation_plan.events, creation_plan.citations):
        for new in group:
            if not dry:
                vault.write_atomic(new.path, new.text())
            written.append(new)
    return written


def write_relationships(changes, existing_notes, creation_plan,
                        dry: bool = True) -> list:
    """Apply the relationship diff, one rewrite per note. Returns the paths."""
    by_xref = {}
    for note in existing_notes:
        ext = note.scalar("external_id")
        if ext:
            by_xref[ext] = note
    path_by_xref = {n.fm["external_id"]: n.path for n in creation_plan.people}

    touched = []
    for xref, diff in changes.items():
        note = by_xref.get(xref)
        if note is None:
            path = path_by_xref.get(xref)
            if path is None or not os.path.exists(path):
                continue
            note = vault.parse(path)
        for key, value in diff.items():
            note.set(key, value)
        if note.dirty:
            touched.append(note.path)
            if not dry:
                note.save()
    return touched


def rebuild_citation_lists(cfg, dry: bool = True) -> list:
    """Recompute every Person's `citations:` from the Citation notes.

    The vault model: recompute this rather than trusting it -- match each Citation's
    `subject_id` to a Person's `cr_id`. The plugin's importer appends, which
    is how the list rots. Returns the paths rewritten.

    Two directions fail, and both are fixed here: an entry pointing at no
    Citation, and a Citation missing from its subject's list. A list that
    recomputes to nothing has its key removed -- an emptied list means the key
    no longer applies.

    Membership is the invariant, not order. A list holding exactly the right
    entries in another order is left alone: rewriting it to this function's
    sort would churn every Person note that has citations and bury the real
    change in the diff.
    """
    people = list(vault.iter_notes(cfg.people))
    by_crid = {n.scalar("cr_id"): n for n in people if n.scalar("cr_id")}
    wanted: dict = {}
    for cit in vault.iter_notes(cfg.citations):
        owner = by_crid.get(cit.scalar("subject_id"))
        if owner is not None:
            wanted.setdefault(owner.path, []).append(cit.basename)

    touched = []
    for note in people:
        have = sorted(str(x) for x in note.as_list("citations"))
        want = [f"[[{n}]]" for n in sorted(wanted.get(note.path, []))]
        if have == want:
            continue
        if want:
            note.set("citations", want)
        else:
            note.remove("citations")
        if note.dirty:
            touched.append(note.path)
            if not dry:
                note.save()
    return touched
