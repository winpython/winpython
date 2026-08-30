"""Which updates to a built set are worth taking, and which are not yet.

    python check_updates.py                          # newest 3.14 slim lockfile
    python check_updates.py --lock <pylock.toml> --min-days 21

Answers the two questions that otherwise mean reading `pip list -o` by eye:

  security   the installed version has an advisory. Always shown, whatever its
             age, with the version that fixes it.
  ready      something newer exists, it has stood at least --min-days without
             being replaced, it is not yanked, and it still has a wheel for
             this target. Standing unpatched is the free half of "the ecosystem
             moved to it"; the download half needs an API key and is not here.
  too new    newer exists but has not aged yet -- shown with the wait left, so
             a version that is nearly ripe is not silently dropped.

Everything comes from PyPI's public JSON: two calls per package, no key. The
installed set comes from a lockfile, so this describes a distribution that was
actually built rather than whatever is installed here.
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
    if not stamps:
        return None
    return datetime.fromisoformat(min(stamps).replace("Z", "+00:00"))


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


def inspect(name: str, installed: str, target: str, now: datetime) -> dict:
    row = {"name": name, "installed": installed, "state": "unknown",
           "candidate": "", "days": 0, "since": 0, "wheels": "", "note": "",
           "requires": []}

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
    newer = {v: f for v, f in usable.items() if version_key(v) > version_key(installed)}

    if advisories:
        fixes = sorted({v for a in advisories for v in (a.get("fixed_in") or [])},
                       key=version_key)
        row["state"] = "security"
        row["candidate"] = next((v for v in fixes if version_key(v) > version_key(installed)),
                                max(newer, key=version_key) if newer else "")
        if not row["candidate"]:
            row["note"] = "NO FIXED VERSION PUBLISHED -- "
        row["note"] += ", ".join(sorted({a.get("id", "?") for a in advisories}))[:70]
    elif not newer:
        row["state"] = "current"
        return row
    else:
        row["candidate"] = max(newer, key=version_key)
        row["state"] = "ready"

    if row["candidate"] and row["candidate"] in releases:
        when = released(releases[row["candidate"]])
        if when:
            row["days"] = (now - when).days
        row["wheels"] = wheel_note(releases[row["candidate"]], target)
    row["since"] = len(newer)
    return row


def caps_from(rows: list[dict]) -> dict[str, list[tuple]]:
    """Who caps whom, extras included.

    A cap hidden behind an extra is the kind that is hardest to see by hand --
    it is absent from constraints.txt, from `pip list -o`, and from a reverse
    dependency tree that evaluates markers with no extra set. It is exactly the
    kind that quietly holds a package down, so record it and say who.
    """
    try:
        from packaging.requirements import InvalidRequirement, Requirement
    except ImportError:
        return {}
    caps: dict[str, list[tuple]] = {}
    for row in rows:
        for text in row["requires"]:
            try:
                requirement = Requirement(text)
            except InvalidRequirement:
                continue
            if not requirement.specifier:
                continue
            marker = str(requirement.marker) if requirement.marker else ""
            extra = ""
            if "extra" in marker:
                # markers stringify as: extra == "autopep8"
                extra = marker.split("==")[-1].strip().strip(QUOTES) if "==" in marker else "?"
            caps.setdefault(normalize(requirement.name), []).append(
                (row["name"], row["installed"], requirement.specifier, extra,
                 set(requirement.extras)))
    return caps


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lock", type=Path, help="pylock.toml describing the built set")
    parser.add_argument("--target", default="cp314", help="interpreter tag to check wheels for")
    parser.add_argument("--min-days", type=int, default=21,
                        help="how long a release must have stood to count as ready")
    parser.add_argument("--jobs", type=int, default=12)
    parser.add_argument("--out", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    lock = args.lock
    if lock is None:
        candidates = sorted(Path("winpython/portable").glob("cycle_*/pylock.64-*slim*.toml"))
        if not candidates:
            print("no slim lockfile found; pass --lock", file=sys.stderr)
            return 2
        lock = candidates[-1]
    if not lock.is_file():
        print(f"no such lockfile: {lock}", file=sys.stderr)
        return 2

    data = tomllib.loads(lock.read_text(encoding="utf-8"))
    installed = {p["name"]: p["version"] for p in data.get("packages", [])}
    now = datetime.now(timezone.utc)
    print(f"{lock.name}: {len(installed)} packages, target {args.target}, "
          f"ripe at {args.min_days} days\nquerying PyPI...", flush=True)

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        rows = list(pool.map(lambda kv: inspect(*kv, args.target, now), installed.items()))

    caps = caps_from(rows)
    for row in rows:
        if row["state"] == "ready" and row["days"] < args.min_days:
            row["state"] = "too new"
        if row["state"] in ("ready", "security") and row["candidate"]:
            blockers = [(who, ver, spec, extra)
                        for who, ver, spec, extra, _ in caps.get(normalize(row["name"]), [])
                        if not spec.contains(row["candidate"], prereleases=True)]
            if blockers:
                who, ver, spec, extra = blockers[0]
                row["state"] = "blocked"
                via = f"[{extra}]" if extra else ""
                # one hop further: the capping package is rarely the one to argue
                # with -- name whoever asked for it, since that is what must change.
                # When the cap is gated on an extra, only a dependant that asked
                # for that extra actually triggers it.
                asked = [w for w, _, _, _, extras in caps.get(normalize(who), [])
                         if w.lower() != row["name"].lower()
                         and (not extra or extra in extras)]
                if asked:
                    origin = f", pulled in by {asked[0]}"
                elif extra:
                    # nothing in the set asks for that extra, so the cap is
                    # declared but probably inert -- worth checking, not obeying
                    origin = f", but nothing requests [{extra}] -- may not bind"
                else:
                    origin = ""
                row["note"] = (f"capped by {who} {ver}{via} requiring {row['name']}{spec}{origin}"
                               + (f" -- {row['note']}" if row["note"] else ""))

    order = {"security": 0, "ready": 1, "blocked": 2, "too new": 3, "unknown": 4, "current": 5}
    rows.sort(key=lambda r: (order[r["state"]], -r["days"], r["name"]))
    groups = {s: [r for r in rows if r["state"] == s] for s in order}

    lines = [f"# update review for {lock.name}, generated {now:%Y-%m-%d}",
             f"# {len(installed)} packages; ready = stood {args.min_days}+ days unreplaced",
             "#",
             "# Data lines are constraint bumps, ready to paste; everything else is a",
             "# comment. 'since' counts releases published after the installed one --",
             "# a high count means the project moves fast, not that this one is risky.",
             ""]
    for state, title in (("security", "SECURITY -- advisory against the installed version"),
                         ("ready", "READY -- aged, unreplaced, still has a wheel"),
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
        print(f"    SECURITY {r['name']} {r['installed']} -> {r['candidate']}  {r['note']}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
