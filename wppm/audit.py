# -*- coding: utf-8 -*-
"""Known security advisories for a set of pinned packages, from osv.dev.

One batch query covers the whole set; details are fetched only for the hits.
Needs network access, no key.
"""
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    from packaging.version import Version
except ImportError:
    from pip._vendor.packaging.version import Version

OSV = "https://api.osv.dev/v1"
TIMEOUT = 30
BATCH = 1000  # osv.dev limit per querybatch


def _call(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.load(response)


def pins_from_file(path):
    """(name, version) pairs of a pylock.toml or of the `name==version` lines of a requirements file."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".toml":
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        return [(p["name"], p["version"]) for p in tomllib.loads(text).get("packages", []) if p.get("version")]
    pins = []
    for line in text.splitlines():
        match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*===?\s*([^\s;#\\]+)", line)
        if match:
            pins.append(match.groups())
    return pins


def _fixed_in(vuln, name, installed):
    """Lowest version that fixes `vuln` above `installed`, '' when none is known."""
    normal = re.sub(r"[-_.]+", "-", name).lower()
    fixes = []
    for affected in vuln.get("affected", []):
        package = affected.get("package", {})
        if package.get("ecosystem") != "PyPI" or re.sub(r"[-_.]+", "-", package.get("name", "")).lower() != normal:
            continue
        for span in affected.get("ranges", []):
            for event in span.get("events", []):
                try:
                    if "fixed" in event and Version(event["fixed"]) > Version(installed):
                        fixes.append(Version(event["fixed"]))
                except Exception:
                    pass
    return str(min(fixes)) if fixes else ""


def audit(pins):
    """Advisories per pinned package: [{package, version, id, aliases, fixed, summary}], sorted.

    The same flaw is often published twice (PYSEC and GHSA, aliases of each
    other): it is reported once. A PYSEC record whose GHSA alias does not match
    the same version is dropped: PYSEC often marks every version affected when
    only a git commit is known as the fix, GHSA carries the curated range.
    """
    pins = sorted(set(pins), key=lambda p: p[0].lower())
    hits = []
    for start in range(0, len(pins), BATCH):
        chunk = pins[start:start + BATCH]
        queries = [{"package": {"name": n, "ecosystem": "PyPI"}, "version": v} for n, v in chunk]
        answers = _call(f"{OSV}/querybatch", {"queries": queries}).get("results", [])
        for (name, version), answer in zip(chunk, answers):
            hits += [(name, version, v["id"]) for v in answer.get("vulns") or []]
    with ThreadPoolExecutor(8) as pool:
        details = dict(zip((h[2] for h in hits), pool.map(lambda h: _call(f"{OSV}/vulns/{h[2]}"), hits)))
    rows, seen = [], set()
    for name, version, vid in sorted(hits, key=lambda h: (h[0].lower(), not h[2].startswith("GHSA"), h[2])):
        vuln = details[vid]
        aliases = [a for a in vuln.get("aliases", []) if a != vid]
        if (name, vid) in seen:
            continue
        if vid.startswith("PYSEC") and any(a.startswith("GHSA") for a in aliases):
            continue   # its GHSA alias was not a hit, or it would be in seen
        seen.update((name, a) for a in [vid] + aliases)
        rows.append({"package": name, "version": version, "id": vid, "aliases": aliases,
                     "fixed": _fixed_in(vuln, name, version),
                     "summary": vuln.get("summary") or (vuln.get("details") or "").split("\n")[0]})
    return rows
