"""Date forms: GEDCOM in, Charted Roots out.

Two consumers read a date differently, so a sync writes two forms:

* **Person `born` / `died`** are checked by the plugin's *Validate date
  formats* command (`plugin_error` replicates it). It accepts ISO or
  `D MMM YYYY` dates, a `c.` / `ca.` / `circa` / `~` prefix, and `a to b`
  ranges -- and nothing for "before" or "after". So `ABT 1804` is written
  `c. 1804`, a range `1850 to 1858`, and `BEF` / `AFT` is dropped from the
  Person: the qualifier stays on the Event, which the command does not check.
* **Event `date`** keeps the vault's own forms: bare ISO with
  `date_precision`, `BEF` / `AFT` kept, `YYYY-YYYY` for a range.

`meaning` reads any of these back to one comparable value, so a pure
spelling difference between them is never reported as a conflict.
"""

from __future__ import annotations

import calendar
import datetime
import re

#: English, plus the German forms upstream trees carry from transcribed
#: records (`25 Dez 1914`, `15 Okt 1795`). Keyed on the first three letters.
MONTHS = {m: i + 1 for i, m in enumerate(
    "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
MONTHS.update({"JÄN": 1, "MÄR": 3, "MRZ": 3, "MAI": 5, "OKT": 10, "DEZ": 12})

#: Prefix -> qualifier. Longest first so `CA.` is not read as `C.`.
_PREFIXES = [
    ("CIRCA", "ABT"), ("ABOUT", "ABT"), ("ABT", "ABT"), ("CAL", "ABT"),
    ("EST", "ABT"), ("CIR", "ABT"), ("CA.", "ABT"), ("C.", "ABT"), ("~", "ABT"),
    ("BEFORE", "BEF"), ("BEF", "BEF"), ("AFTER", "AFT"), ("AFT", "AFT"),
]

_ISO_FULL = re.compile(r'^(\d{4})-(\d{1,2})-(\d{1,2})$')
_ISO_MONTH = re.compile(r'^(\d{4})-(\d{1,2})$')
_YEAR = re.compile(r'^(\d{3,4})$')
_DMY_TEXT = re.compile(r'^(\d{1,2})\s*([^\W\d_]{3})[^\W\d_]*\.?\s*(\d{3,4})$')
_MY_TEXT = re.compile(r'^([^\W\d_]{3})[^\W\d_]*\.?\s+(\d{3,4})$')
_DMY_DOTS = re.compile(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$')
_YEAR_SPAN = re.compile(r'^(\d{4})\s*-\s*(\d{4})$')
#: Range forms, matched against the upper-cased text.
_BET_AND = re.compile(r'^BET\.?\s+(.+?)\s+AND\s+(.+)$')
_FROM_TO = re.compile(r'^FROM\s+(.+?)\s+TO\s+(.+)$')


def single(text: str) -> tuple | None:
    """One calendar date -> (ISO value, precision), or None."""
    d = (text or "").strip()
    m = _ISO_FULL.match(d)
    if m:
        return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))), "exact"
    m = _ISO_MONTH.match(d)
    if m and 1 <= int(m.group(2)) <= 12:
        return "%s-%02d" % (m.group(1), int(m.group(2))), "month"
    m = _YEAR.match(d)
    if m:
        return "%04d" % int(m.group(1)), "year"
    m = _DMY_TEXT.match(d)
    if m and m.group(2).upper() in MONTHS:
        return "%04d-%02d-%02d" % (int(m.group(3)), MONTHS[m.group(2).upper()],
                                   int(m.group(1))), "exact"
    m = _MY_TEXT.match(d)
    if m and m.group(1).upper() in MONTHS:
        return "%04d-%02d" % (int(m.group(2)), MONTHS[m.group(1).upper()]), "month"
    m = _DMY_DOTS.match(d)
    if m and 1 <= int(m.group(2)) <= 12:
        return "%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1))), "exact"
    return None


def _strip_prefix(text: str) -> tuple:
    up = text.upper()
    for prefix, qual in _PREFIXES:
        if up.startswith(prefix):
            rest = text[len(prefix):]
            if prefix[-1].isalpha():
                if rest[:1] not in (".", " ", ""):
                    continue      # `CALIF…`, not `CAL`
                rest = rest.lstrip(".")
            return qual, rest.strip()
    return "", text.strip()


def _span(a: str, b: str) -> tuple | None:
    sa, sb = single(a), single(b)
    if not (sa and sb):
        return None
    ya, yb = sa[0][:4], sb[0][:4]
    return (ya, yb) if ya != yb else (ya, "")


def from_gedcom(raw: str) -> tuple:
    """GEDCOM date -> (Event form, date_precision).

    Event forms: ISO, `ABT <iso>`, `BEF <iso>`, `AFT <iso>`, `YYYY-YYYY`.
    Anything unreadable comes back verbatim with precision `unknown`; the
    Person form of such a value is empty, so it is never written there.
    """
    if not raw or not raw.strip():
        return "", "unknown"
    d = raw.strip()
    up = d.upper()
    m = _BET_AND.match(up) or _FROM_TO.match(up) or _YEAR_SPAN.match(d)
    if m:
        span = _span(m.group(1), m.group(2))
        if span:
            return ("%s-%s" % span if span[1] else span[0]), "range"
        return d, "unknown"
    qual, rest = _strip_prefix(d)
    one = single(rest)
    if one is None:
        return d, "unknown"
    if qual:
        return f"{qual} {one[0]}", "estimated"
    return one


def meaning(value) -> tuple | None:
    """Any vault or GEDCOM date form -> (qualifier, start, end), or None.

    `ABT 1804`, `c. 1804` and `circa 1804` read the same; so do `1850-1858`,
    `1850 to 1858` and `BET 1850 AND 1858`.
    """
    v = str(value or "").strip()
    if not v:
        return None
    up = v.upper()
    m = (_BET_AND.match(up)
         or re.match(r'^(?:FROM\s+)?(.+?)\s+TO\s+(.+)$', up)
         or _YEAR_SPAN.match(v))
    if m:
        a, b = single(m.group(1)), single(m.group(2))
        return ("", a[0], b[0]) if a and b else None
    qual, rest = _strip_prefix(v)
    one = single(rest)
    return (qual, one[0], "") if one else None


def person_form(value: str) -> str:
    """The `born` / `died` form of a date, clean under the plugin's validator.

    '' when there is nothing safe to write. `BEF` / `AFT` become the bare
    date: the validator has no form for them, and the Event keeps the
    qualifier.
    """
    m = meaning(value)
    if m is None:
        return ""
    qual, start, end = m
    if end:
        return f"{start} to {end}"
    if qual == "ABT":
        return f"c. {start}"
    return start


# -- classify / bounds: how a validator reads a raw GEDCOM date -------------

_EN_MONTHS = tuple(MONTHS)[:12]
_G_DATE = r'(?:(?:\d{1,2}\s+)?(?:' + "|".join(_EN_MONTHS) + r')\s+)?\d{3,4}'
#: GEDCOM 5.5.1 grammar, English months only (case is ignored).
_G_STRICT = re.compile(
    r'^(?:%(d)s|(?:ABT|CAL|EST|BEF|AFT)\s+%(d)s|BET\s+%(d)s\s+AND\s+%(d)s'
    r'|FROM\s+%(d)s\s+TO\s+%(d)s)$' % {"d": _G_DATE}, re.I)
#: Valid GEDCOM that `from_gedcom` returns as `unknown`.
_G_UNPARSED = re.compile(
    r'^(?:\(.*\)|INT\s+.+\(.*\)|@#D.*|(?:FROM|TO)\s+%s)$' % _G_DATE, re.I)
_G_BC = re.compile(r'B\.C\.?$', re.I)
_G_DUAL = re.compile(r'(?<![\d/])\d{3,4}/\d{2}(?![\d/])')
#: `Abt.` / `BET.` and friends: a dot after a GEDCOM keyword counts like case.
_G_KEYWORD_DOT = re.compile(
    r'\b(ABT|BEF|AFT|CAL|EST|BET|AND|FROM|TO|INT)\.(?=\s|$)', re.I)
_CAL_EST = re.compile(r'^(CAL|EST)(?![A-Z])')


def _read(d: str) -> tuple | None:
    """Mirror `from_gedcom`: (qualifier, range kind, [single results]) or None."""
    up = d.upper()
    for kind, m in (("BET", _BET_AND.match(up)), ("FROM", _FROM_TO.match(up)),
                    ("SPAN", _YEAR_SPAN.match(d))):
        if m:
            parts = [single(m.group(1)), single(m.group(2))]
            return ("", kind, parts) if all(parts) else None
    qual, rest = _strip_prefix(d)
    one = single(rest)
    if one is None:
        return None
    cal = _CAL_EST.match(up)
    return (cal.group(1) if cal else qual), "", [one]


def _on_calendar(iso: str) -> bool:
    bits = [int(b) for b in iso.split("-")]
    try:
        datetime.date(bits[0], *(bits[1:] + [1, 1][len(bits) - 1:]))
    except ValueError:
        return False
    return True


def _spell(one: tuple) -> str:
    iso, precision = one
    y, *rest = iso.split("-")
    if precision == "year":
        return y
    mon = _EN_MONTHS[int(rest[0]) - 1]
    return "%d %s %s" % (int(rest[1]), mon, y) if precision == "exact" else f"{mon} {y}"


def classify(raw: str) -> tuple:
    """Raw GEDCOM date -> (label, suggestion).

    Labels: `empty`, `standard` (5.5.1 grammar and `from_gedcom` reads it),
    `standard-unparsed` (valid grammar `from_gedcom` cannot read), `invalid`
    (reads, but not a calendar day), `lenient` (reads, but is not 5.5.1;
    the suggestion is the 5.5.1 spelling) and `unreadable`.
    """
    d = (raw or "").strip()
    if not d:
        return "empty", ""
    if (_G_UNPARSED.match(d) or _G_BC.search(d) or _G_DUAL.search(d)):
        return "standard-unparsed", ""
    read = _read(d)
    if read is None:
        return "unreadable", ""
    qual, kind, parts = read
    if not all(_on_calendar(p[0]) for p in parts):
        return "invalid", ""
    if _G_STRICT.match(_G_KEYWORD_DOT.sub(r'\1', d)):
        return "standard", ""
    spelled = [_spell(p) for p in parts]
    if kind:
        return "lenient", ("BET %s AND %s" if kind == "SPAN" or kind == "BET"
                           else "FROM %s TO %s") % tuple(spelled)
    return "lenient", f"{qual} {spelled[0]}".strip()


def _extent(one: tuple) -> tuple:
    iso, precision = one
    if precision == "exact":
        return iso, iso
    y, m = int(iso[:4]), (int(iso[5:7]) if precision == "month" else None)
    if m is None:
        return "%04d-01-01" % y, "%04d-12-31" % y
    return "%04d-%02d-01" % (y, m), "%04d-%02d-%02d" % (y, m, calendar.monthrange(y, m)[1])


def bounds(raw: str) -> tuple:
    """Earliest and latest ISO day a date can mean, or (None, None).

    Generous on purpose: `ABT` is +/-10 years, `BEF` / `AFT` are open-ended.
    Dates that do not classify as standard or lenient have no bounds.
    """
    if classify(raw)[0] not in ("standard", "lenient"):
        return None, None
    qual, kind, parts = _read(raw.strip())
    ext = [_extent(p) for p in parts]
    lo, hi = min(e[0] for e in ext), max(e[1] for e in ext)
    if qual == "BEF":
        return None, hi
    if qual == "AFT":
        return lo, None
    if qual in ("ABT", "CAL", "EST"):
        return ("%04d-01-01" % max(int(lo[:4]) - 10, 1),
                "%04d-12-31" % min(int(hi[:4]) + 10, 9999))
    return lo, hi


# -- the plugin's "Validate date formats" command ---------------------------

_CIRCA = ("c.", "ca.", "circa", "~")
_V_ISO = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')
_V_ISO_LOOSE = re.compile(r'^(\d{4})-(\d{1,2})-(\d{1,2})$')
_V_MONTH = re.compile(r'^(\d{4})-(\d{2})$')
_V_YEAR = re.compile(r'^(\d{4})$')
_MON = "JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC"
_V_GED = re.compile(r'^(\d{1,2})\s+(' + _MON + r')\s+(\d{4})$', re.I)
_V_GED_MONTH = re.compile(r'^(' + _MON + r')\s+(\d{4})$', re.I)


def _plugin_single(a: str, s: dict) -> str:
    partial = s.get("allowPartialDates", True)
    zeros = s.get("requireLeadingZeros", False)
    std = s.get("dateFormatStandard", "flexible")
    if std == "iso8601":
        if zeros:
            ok = _V_ISO.match(a) or partial and (_V_MONTH.match(a) or _V_YEAR.match(a))
            return "" if ok else "ISO 8601 format required with leading zeros (YYYY-MM-DD)"
        ok = _V_ISO.match(a) or _V_ISO_LOOSE.match(a) or partial and (
            _V_MONTH.match(a) or _V_YEAR.match(a))
        return "" if ok else "ISO 8601 format required (YYYY-MM-DD or YYYY-M-D)"
    if std == "gedcom":
        ok = _V_GED.match(a) or partial and (_V_GED_MONTH.match(a) or _V_YEAR.match(a))
        return "" if ok else "GEDCOM format required (DD MMM YYYY, e.g., 15 JAN 1920)"
    if std == "flexible":
        ok = (_V_ISO.match(a) or not zeros and _V_ISO_LOOSE.match(a)
              or partial and (_V_MONTH.match(a) or _V_YEAR.match(a))
              or _V_GED.match(a) or partial and _V_GED_MONTH.match(a))
        return "" if ok else "Unrecognized date format (expected YYYY-MM-DD or DD MMM YYYY)"
    return "Unknown date format standard"


def plugin_error(value: str, settings: dict) -> str:
    """The plugin's verdict on a `born` / `died` value: '' if it passes.

    A line-for-line port of Charted Roots' date validator (`Sse` / `Tse` in
    the vendored `main.js`), driven by the same `data.json` settings. Keep
    it a port: its odd corners (no before/after form, a hyphenated year
    span rejected) are what the command actually reports.
    """
    t = str(value).strip()
    low = t.lower()
    circa = any(low.startswith(p) for p in _CIRCA)
    if circa and not settings.get("allowCircaDates", True):
        return 'Circa dates not allowed (check "Allow circa dates" setting)'
    i = t
    if circa:
        for p in _CIRCA:
            if i.lower().startswith(p):
                i = i[len(p):].strip()
                break
    parts = i.split("-")
    ranged = " to " in i or ("-" in i and len(parts) == 3 and len(parts[2]) == 4)
    if ranged and not settings.get("allowDateRanges", True):
        return 'Date ranges not allowed (check "Allow date ranges" setting)'
    if ranged:
        for piece in (i.split(" to ") if " to " in i else parts[:2]):
            err = _plugin_single(piece.strip(), settings)
            if err:
                return err
        return ""
    return _plugin_single(i, settings)
