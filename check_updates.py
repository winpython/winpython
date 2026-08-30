"""Which updates to a built set are worth taking, and which are not yet.

    python check_updates.py                          # newest 3.14 slim lockfile
    python check_updates.py --lock <pylock.toml> --target cp314 --min-days 21

Answers the questions that otherwise mean reading `pip list -o` by eye:

  security   the installed version has an advisory. Always shown, whatever its
             age, and the version offered is the first one with **no** advisory
             of its own -- the minimum `fixed_in` often carries later ones.
  ready      something newer exists, it has stood at least --min-days without
             being replaced, it is not yanked, it still has a wheel for this
             target, nothing in the set caps it, and the wheelhouse holds what
             it needs. Standing unpatched is the free half of "the ecosystem
             moved to it"; the download half needs an API key and is not here.
  blocked    something in the set requires a version range that excludes it.
  needs      nothing forbids it, but the wheelhouse lacks a dependency it wants,
             so a local build would quietly backtrack to the old version.
  too new    newer exists but has not aged yet, shown with the wait left.

A pinned version gets held down in three different ways, and all three are
checked here because each is invisible to a different tool:

  * an unconditional cap, e.g. msal -> cryptography<49. Visible in metadata.
  * a cap behind an extra, e.g. spyder -> python-lsp-server[all] -> autopep8
    <2.1.0. Absent from constraints.txt, from `pip list -o`, and from a reverse
    dependency tree evaluated with no extra set.
  * a dependency missing from the wheelhouse. Since a local build resolves with
    --no-index --find-links, pip silently backtracks until the requirements can
    be met, and nothing anywhere reports a conflict.

Everything comes from PyPI's public JSON, no key needed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import tomllib
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

PYPI = "https://pypi.org/pypi"
TIMEOUT = 30
QUOTES = "\"'"
PRERELEASE = re.compile(r"(a|b|rc|dev)\d", re.I)
# How far past the first claimed fix to look for a release with no advisory.
# A busy project can put a dozen releases between the two -- pypdf needed
# eleven -- and stopping short offers a version that is still vulnerable.
CLEAN_PROBES = 24

try:
    from packaging.requirements import InvalidRequirement, Requirement
except ImportError:
    Requirement = None


def normalize(name: str) -> str:
    """PEP 503 normalized project name."""
    return re.sub(r"[-_.]+", "-", name).lower()


def version_key(text: str):
    """Sortable version key, tolerating anything unparseable."""
    try:
        from packaging.version import InvalidVersion, Version
        try:
            return (1, Version(text))
        except InvalidVersion:
            pass
    except ImportError:
        pass
    return (0, tuple(int(p) if p.isdigit() else p for p in re.split(r"[._-]", text)))


def is_prerelease(text: str) -> bool:
    try:
        from packaging.version import InvalidVersion, Version
        try:
            return Version(text).is_prerelease
        except InvalidVersion:
            pass
    except ImportError:
        pass
    return bool(PRERELEASE.search(text))


def fetch(url: str, attempts: int = 3):
    """PyPI JSON, retried: one dropped connection must not read as 'no such package'."""
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            pass
        if attempt + 1 < attempts:
            time.sleep(1 + attempt)
    return None


def released(files: list[dict]) -> datetime | None:
    stamps = [f["upload_time_iso_8601"] for f in files if f.get("upload_time_iso_8601")]
    return datetime.fromisoformat(min(stamps).replace("Z", "+00:00")) if stamps else None


def wheel_note(files: list[dict], target: str) -> str:
    """How this release covers the target interpreter, e.g. cp314 or cp314t."""
    names = [f["filename"] for f in files if f["filename"].endswith(".whl")]
    if not names:
        return "sdist only"
    if any(f"-{target}-" in n and "win_amd64" in n for n in names):
        return "wheel"
    if any("abi3" in n and "win_amd64" in n for n in names):
        return "abi3" if target.endswith("t") else "wheel"
    if any("py3-none-any" in n or "py2.py3-none-any" in n for n in names):
        return "pure"
    return "no win wheel"


def first_clean(name: str, ordered: list[str], start: str) -> tuple[str, str]:
    """The first release at or above `start` with no advisory of its own.

    The minimum version in an advisory's `fixed_in` only fixes what was filed
    against the *installed* version; later advisories are commonly filed against
    it in turn. pypdf 6.10.2 carried 29, its claimed fix 6.12.0 still carried 25,
    and the first clean release was 6.15.0.
    """
    probes = [v for v in ordered if version_key(v) >= version_key(start)][:CLEAN_PROBES]
    for version in probes:
        data = fetch(f"{PYPI}/{name}/{version}/json")
        if data is None:
            continue
        if not (data.get("vulnerabilities") or []):
            return version, ""
    if probes:
        return probes[-1], f"still has advisories at {probes[-1]}"
    return start, ""


def inspect(name: str, installed: str, target: str, now: datetime) -> dict:
    row = {"name": name, "installed": installed, "state": "unknown", "candidate": "",
           "days": 0, "since": 0, "wheels": "", "note": "", "requires": [],
           "candidate_requires": [], "missing": []}

    meta = fetch(f"{PYPI}/{name}/json")
    vuln = fetch(f"{PYPI}/{name}/{installed}/json")
    if meta is None:
        row["note"] = "not on PyPI (or fetch failed)"
        return row

    row["requires"] = ((vuln or {}).get("info") or {}).get("requires_dist") or []
    advisories = (vuln or {}).get("vulnerabilities") or []
    releases = meta.get("releases", {})
    usable = {v: f for v, f in releases.items()
              if f and not is_prerelease(v) and not all(x.get("yanked") for x in f)}
    newer = sorted((v for v in usable if version_key(v) > version_key(installed)),
                   key=version_key)

    if advisories:
        row["state"] = "security"
        fixes = sorted({v for a in advisories for v in (a.get("fixed_in") or [])},
                       key=version_key)
        claimed = next((v for v in fixes if version_key(v) > version_key(installed)),
                       newer[-1] if newer else "")
        if claimed:
            # do not stop at the claimed fix -- it often carries later advisories
            row["candidate"], caveat = first_clean(name, newer, claimed)
            if caveat:
                row["note"] = caveat + " -- "
        else:
            row["note"] = "NO FIXED VERSION PUBLISHED -- "
        row["note"] += ", ".join(sorted({a.get("id", "?") for a in advisories}))[:70]
    elif not newer:
        row["state"] = "current"
        return row
    else:
        row["candidate"] = newer[-1]
        row["state"] = "ready"

    if row["candidate"] and row["candidate"] in releases:
        when = released(releases[row["candidate"]])
        if when:
            row["days"] = (now - when).days
        row["wheels"] = wheel_note(releases[row["candidate"]], target)
        info = fetch(f"{PYPI}/{name}/{row['candidate']}/json") or {}
        row["candidate_requires"] = (info.get("info") or {}).get("requires_dist") or []
    row["since"] = len(newer)
    return row


def parse_requires(texts: list[str]):
    """(Requirement, gating extra) for each parseable entry."""
    if Requirement is None:
        return
    for text in texts:
        try:
            requirement = Requirement(text)
        except InvalidRequirement:
            continue
        marker = str(requirement.marker) if requirement.marker else ""
        extra = ""
        if "extra" in marker:
            # markers stringify as: extra == "autopep8"
            extra = marker.split("==")[-1].strip().strip(QUOTES) if "==" in marker else "?"
        yield requirement, extra


def target_environment(target: str) -> dict[str, str]:
    """A marker environment for the interpreter being built, on Windows.

    Without this, a dependency gated on an old python_version -- redis wanting
    async-timeout below 3.11.3, say -- reads as missing when the target will
    never ask for it.
    """
    match = re.match(r"cp(\d)(\d+)t?$", target)
    version = f"{match.group(1)}.{match.group(2)}" if match else "3.14"
    return {"python_version": version, "python_full_version": f"{version}.0",
            "sys_platform": "win32", "platform_system": "Windows",
            "platform_machine": "AMD64", "os_name": "nt",
            "implementation_name": "cpython", "platform_python_implementation": "CPython"}


def wanted_here(requirement, extra: str, environment: dict) -> bool:
    """Does this requirement apply to the interpreter we are building for?"""
    if requirement.marker is None:
        return True
    try:
        return bool(requirement.marker.evaluate({**environment, "extra": extra}))
    except Exception:
        return True


def survey(rows: list[dict]) -> tuple[dict, dict]:
    """Version caps declared anywhere in the set, and which extras are asked for."""
    caps: dict[str, list[tuple]] = {}
    wanted_extras: dict[str, set[str]] = {}
    for row in rows:
        for requirement, extra in parse_requires(row["requires"]):
            key = normalize(requirement.name)
            # Only an unconditionally active requirement really asks for an
            # extra. A gated one does not -- and packages routinely declare
            # `self[test]; extra == "all"`, which would otherwise make every
            # development extra look like part of the distribution.
            if requirement.extras and not extra:
                wanted_extras.setdefault(key, set()).update(requirement.extras)
            if requirement.specifier:
                caps.setdefault(key, []).append(
                    (row["name"], row["installed"], requirement.specifier, extra,
                     set(requirement.extras)))
    return caps, wanted_extras


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lock", type=Path, help="pylock.toml describing the built set")
    parser.add_argument("--target", default="cp314", help="interpreter tag to check wheels for")
    parser.add_argument("--min-days", type=int, default=21,
                        help="how long a release must have stood to count as ready")
    parser.add_argument("--wheelhouse", type=Path, default=Path(r"C:\WinP\packages.srcreq"),
                        help="local index a build resolves against; '' to skip that check")
    parser.add_argument("--jobs", type=int, default=12)
    parser.add_argument("--out", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    lock = args.lock
    if lock is None:
        found = sorted(Path("winpython/portable").glob("cycle_*/pylock.64-*slim*.toml"))
        if not found:
            print("no slim lockfile found; pass --lock", file=sys.stderr)
            return 2
        lock = found[-1]
    if not lock.is_file():
        print(f"no such lockfile: {lock}", file=sys.stderr)
        return 2

    available: set[str] = set()
    if args.wheelhouse and str(args.wheelhouse) and args.wheelhouse.is_dir():
        for path in args.wheelhouse.iterdir():
            if path.suffix == ".whl":
                available.add(normalize(path.name.split("-")[0]))
            elif path.name.endswith((".tar.gz", ".zip")):
                stem = re.sub(r"-\d.*$", "", path.name)
                available.add(normalize(stem))

    data = tomllib.loads(lock.read_text(encoding="utf-8"))
    installed = {p["name"]: p["version"] for p in data.get("packages", [])}
    now = datetime.now(timezone.utc)
    print(f"{lock.name}: {len(installed)} packages, target {args.target}, "
          f"ripe at {args.min_days} days"
          + (f", wheelhouse {len(available)} projects" if available else "")
          + "\nquerying PyPI...", flush=True)

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        rows = list(pool.map(lambda kv: inspect(*kv, args.target, now), installed.items()))

    caps, wanted_extras = survey(rows)
    environment = target_environment(args.target)
    for row in rows:
        if row["state"] == "ready" and row["days"] < args.min_days:
            row["state"] = "too new"
        if row["state"] not in ("ready", "security") or not row["candidate"]:
            continue
        key = normalize(row["name"])

        # 1. does anything forbid the candidate outright?
        blockers = [(who, ver, spec, extra, extras)
                    for who, ver, spec, extra, extras in caps.get(key, [])
                    if not spec.contains(row["candidate"], prereleases=True)]
        # an unconditional cap always binds; one behind an extra only binds if
        # something asked for that extra, so rank the certain ones first
        blockers.sort(key=lambda b: (bool(b[3]), b[0]))
        if blockers:
            who, ver, spec, extra, _ = blockers[0]
            via = f"[{extra}]" if extra else ""
            asked = [w for w, _, _, _, extras in caps.get(normalize(who), [])
                     if w.lower() != row["name"].lower() and (not extra or extra in extras)]
            if asked:
                origin = f", pulled in by {asked[0]}"
            elif extra:
                origin = f", but nothing requests [{extra}] -- may not bind"
            else:
                origin = ""
            more = f" (+{len(blockers) - 1} more)" if len(blockers) > 1 else ""
            cap = f"capped by {who} {ver}{via} requiring {row['name']}{spec}{origin}{more}"
            # a security fix you cannot take is still a security problem, so it
            # stays in that section rather than being filed away under blocked
            if row["state"] == "ready":
                row["state"] = "blocked"
            row["note"] = cap + (f" -- {row['note']}" if row["note"] else "")
            continue

        # 2. can the wheelhouse actually satisfy what the candidate wants?
        if available:
            active = wanted_extras.get(key, set())
            missing = sorted({requirement.name
                              for requirement, extra in parse_requires(row["candidate_requires"])
                              if (not extra or extra in active)
                              and wanted_here(requirement, extra, environment)
                              and normalize(requirement.name) not in available})
            if missing:
                row["missing"] = missing
                need = f"wheelhouse lacks {', '.join(missing)}"
                if row["state"] == "ready":
                    row["state"] = "needs"
                    row["note"] = need + (f" -- {row['note']}" if row["note"] else "")
                else:  # a security fix stays visible as such, with the warning attached
                    row["note"] = f"{need} -- {row['note']}"

    order = {"security": 0, "ready": 1, "needs": 2, "blocked": 3,
             "too new": 4, "unknown": 5, "current": 6}
    rows.sort(key=lambda r: (order[r["state"]], -r["days"], r["name"]))
    groups = {s: [r for r in rows if r["state"] == s] for s in order}

    lines = [f"# update review for {lock.name}, generated {now:%Y-%m-%d}",
             f"# {len(installed)} packages; ready = stood {args.min_days}+ days unreplaced",
             "#",
             "# Data lines are constraint bumps, ready to paste; everything else is a",
             "# comment. 'since' counts releases published after the installed one --",
             "# a high count means the project moves fast, not that this one is risky.",
             "# Security candidates are the first release with no advisory of their own,",
             "# not the minimum version the advisories claim as fixed.",
             ""]
    for state, title in (
            ("security", "SECURITY -- advisory against the installed version"),
            ("ready", "READY -- aged, unreplaced, nothing forbids it"),
            ("needs", "NEEDS -- allowed, but the wheelhouse lacks a dependency"),
            ("blocked", "BLOCKED -- something in the set caps it"),
            ("too new", "TOO NEW -- revisit when aged"),
            ("unknown", "COULD NOT CHECK")):
        entries = groups[state]
        lines += ["", f"# --- {title}  ({len(entries)})"]
        if not entries:
            lines += ["#   none"]
            continue
        for r in entries:
            detail = f"{r['installed']} -> {r['candidate']}, {r['days']}d, {r['wheels']}"
            if r["since"] > 1:
                detail += f", {r['since']} releases since"
            if r["note"]:
                detail += f", {r['note']}"
            prefix = "" if state in ("security", "ready") else "# "
            lines += [f"{prefix}{r['name']}>={r['candidate']}   # {detail}"
                      if r["candidate"] else f"# {r['name']}   # {detail}"]

    out = args.out / f"updates.{lock.stem.replace('pylock.', '')}.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    for state in order:
        print(f"  {state:<9}: {len(groups[state]):>4}")
    for r in groups["security"]:
        print(f"    SECURITY {r['name']} {r['installed']} -> {r['candidate']}  {r['note'][:80]}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
