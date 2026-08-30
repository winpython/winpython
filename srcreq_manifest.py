"""Inventory the local wheelhouse, and say which files nothing needs any more.

    python srcreq_manifest.py                       # report + write both lists
    python srcreq_manifest.py --cycle winpython/portable/cycle_2026_04
    python srcreq_manifest.py --delete dead         # actually remove a bucket

The wheelhouse is the index a local build resolves against
(`pip install --no-index --find-links=...`), so what is in it decides what gets
built. Left alone it only grows: versions superseded cycles ago, and packages
no requirement file mentions any longer.

What a build still needs is not a guess -- the shipped lockfiles say it exactly.
A (name, version) pair is `used` when a lockfile installs it, `superseded` when
the project is still in use but that version is not, and `dead` when no
lockfile and no requirement or constraint file names the project at all.

Deleting is safe because the lockfiles are in git: any past distribution can be
refetched with `pip download --require-hashes -r <its pylock>`. Nothing is
deleted without --delete, which names the bucket explicitly.

Hashes come from the lockfiles rather than from the files, so this reads no
package bytes. The build's web-vs-local double lock is what makes that sound:
it already proves the local copies match what PyPI serves.
"""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from collections import defaultdict
from datetime import date
from pathlib import Path

WHEEL = ".whl"
SDIST = (".tar.gz", ".zip", ".tar.bz2")
REQUIREMENT_FILES = ("constraints.txt", "requirements_slim.txt", "requirements_slimf.txt",
                     "dot_requirements.txt", "requirements_whl.txt", "mandatory_requirements.txt")
# A lockfile whose name still carries a release level (b0, b1, ...) is from a
# superseded build of its cycle; the shipped ones have none.
SUPERSEDED_LOCK = re.compile(r"b\d+(_wheels)?\.toml$")
BUCKETS = ("superseded", "dead", "unparsed")


def normalize(name: str) -> str:
    """PEP 503 normalized project name."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_filename(path: Path, known: set[str]) -> tuple[str, str] | None:
    """(normalized name, version) for a wheel or sdist file name, else None.

    Wheel names are unambiguous. Sdist names are not -- a project name may
    contain the same '-' that separates it from the version -- so the longest
    known project name prefixing the file wins, and only when nothing matches
    do we fall back to splitting at the first '-' before a digit.
    """
    name = path.name
    if name.endswith(WHEEL):
        parts = name[: -len(WHEEL)].split("-")
        return (normalize(parts[0]), parts[1]) if len(parts) >= 3 else None

    for suffix in SDIST:
        if name.endswith(suffix):
            stem = name[: -len(suffix)]
            break
    else:
        return None

    candidates = [k for k in known if normalize(stem).startswith(k + "-")]
    if candidates:
        best = max(candidates, key=len)
        return best, stem[len(best) + 1:]
    match = re.match(r"^(.*?)-(\d.*)$", stem)
    return (normalize(match.group(1)), match.group(2)) if match else None


def read_locks(cycle_dirs: list[Path]) -> tuple[dict, dict, list[Path]]:
    """Artifacts the shipped lockfiles install, and which were built from sdist."""
    locks = sorted(p for d in cycle_dirs for p in d.glob("pylock.*.toml")
                   if not SUPERSEDED_LOCK.search(p.name))
    wanted: dict[tuple[str, str], set[str]] = defaultdict(set)
    from_sdist: dict[tuple[str, str], set[str]] = defaultdict(set)
    for lock in locks:
        data = tomllib.loads(lock.read_text(encoding="utf-8"))
        for pkg in data.get("packages", []):
            key = (normalize(pkg["name"]), pkg["version"])
            for artifact in pkg.get("wheels", []):
                if digest := artifact.get("hashes", {}).get("sha256"):
                    wanted[key].add(digest)
            if sdist := pkg.get("sdist"):
                if digest := sdist.get("hashes", {}).get("sha256"):
                    wanted[key].add(digest)
                from_sdist[key].add(lock.name)
    return wanted, from_sdist, locks


def read_declared(repo: Path) -> set[str]:
    """Project names any current requirement or constraint file mentions."""
    names: set[str] = set()
    for filename in REQUIREMENT_FILES:
        path = repo / filename
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line := line.split("#")[0].strip():
                if name := re.split(r"[<>=!~;\[ ]", line)[0].strip():
                    names.add(normalize(name))
    return names


def gigabytes(paths) -> float:
    return sum(p.stat().st_size for p in paths) / 2 ** 30


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--srcreq", type=Path, default=Path(r"C:\WinP\packages.srcreq"),
                        help="the wheelhouse to inventory")
    parser.add_argument("--cycle", type=Path, action="append", dest="cycles",
                        help="cycle directory to read lockfiles from; repeatable, "
                             "defaults to the two newest under winpython/portable")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("."))
    parser.add_argument("--delete", choices=BUCKETS, action="append", dest="delete",
                        help="remove the files in this bucket; repeatable")
    args = parser.parse_args(argv)

    cycles = args.cycles or sorted((args.repo / "winpython/portable").glob("cycle_*"))[-2:]
    if not args.srcreq.is_dir():
        print(f"no such wheelhouse: {args.srcreq}", file=sys.stderr)
        return 2
    missing = [d for d in cycles if not d.is_dir()]
    if missing:
        print(f"no such cycle directory: {missing[0]}", file=sys.stderr)
        return 2

    wanted, from_sdist, locks = read_locks(cycles)
    if not wanted:
        print(f"no lockfiles found under {', '.join(map(str, cycles))}", file=sys.stderr)
        return 2
    live = {name for name, _ in wanted} | read_declared(args.repo)

    files = sorted(p for p in args.srcreq.iterdir() if p.is_file())
    buckets: dict[str, list[Path]] = defaultdict(list)
    labels: dict[Path, tuple[str, str]] = {}
    for path in files:
        parsed = parse_filename(path, live)
        if parsed is None:
            buckets["unparsed"].append(path)
            continue
        labels[path] = parsed
        name, version = parsed
        buckets["used" if (name, version) in wanted
                else "superseded" if name in live else "dead"].append(path)

    on_disk = set(labels.values())
    absent = sorted(set(wanted) - on_disk)
    today = date.today().isoformat()

    manifest = args.out / "srcreq_manifest.txt"
    sdist_note = [f"#   {n}=={v}  built from sdist by {', '.join(sorted(w))}"
                  for (n, v), w in sorted(from_sdist.items())]
    manifest.write_text("\n".join([
        f"# packages.srcreq manifest, generated {today}",
        f"# from {len(locks)} shipped lockfiles in {', '.join(d.as_posix() for d in cycles)}",
        f"# {len(wanted)} (name, version) pairs; regenerate with srcreq_manifest.py",
        "#",
        "# An inventory and a verification list, not a one-command restore: one",
        "# pip download only fetches artifacts matching the interpreter running it,",
        "# so a wheelhouse serving several Pythons needs one pass per target, each",
        "# against that flavor's own pylock:",
        "#",
        "#   pip download --dest <folder> --no-deps --require-hashes -r <pylock.toml>",
        "#",
        *(["# Every line installs from a wheel, with these exceptions:", *sdist_note]
          if sdist_note else ["# No lockfile here builds anything from an sdist."]),
        "",
        *(f"{name}=={version} " +
          " ".join(f"--hash=sha256:{h}" for h in sorted(wanted[(name, version)])).rstrip()
          for name, version in sorted(wanted)),
    ]) + "\n", encoding="utf-8", newline="\n")

    prune = args.out / "srcreq_prune.txt"
    reasons = {
        "superseded": "older version of a package still in use",
        "dead": "no lockfile and no requirement file names this project",
        "unparsed": "not a wheel or sdist name -- look before removing",
    }
    lines = [
        f"# packages.srcreq prune candidates, generated {today}",
        f"# wheelhouse holds {len(files)} files, {gigabytes(files):.1f} GB",
        f"# {len(buckets['used'])} files are installed by a shipped lockfile and are NOT listed",
        "#",
        "# Safe to remove: every pylock is in git, so any past distribution refetches",
        "# with pip download --require-hashes. Remove with --delete <bucket>.",
    ]
    for bucket in BUCKETS:
        if entries := buckets[bucket]:
            lines += ["", f"# --- {bucket}: {reasons[bucket]}",
                      f"# {len(entries)} files, {gigabytes(entries):.2f} GB", ""]
            lines += [p.name for p in sorted(entries, key=lambda p: (labels.get(p, ("", ""))[0], p.name))]
    prune.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(f"lockfiles read   : {len(locks)} from {', '.join(d.name for d in cycles)}")
    print(f"pairs to keep    : {len(wanted)}"
          + (f"   ** {len(absent)} NOT on disk **" if absent else "   all present on disk"))
    for name, version in absent[:10]:
        print(f"                   missing {name}=={version}")
    print(f"wheelhouse       : {len(files)} files, {gigabytes(files):.1f} GB")
    for bucket in ("used", *BUCKETS):
        entries = buckets[bucket]
        print(f"  {bucket:<13}: {len(entries):>5} files, {gigabytes(entries):>5.2f} GB")
    reclaimable = [p for b in BUCKETS for p in buckets[b]]
    if reclaimable:
        print(f"reclaimable      : {gigabytes(reclaimable):.1f} GB "
              f"({gigabytes(reclaimable) / max(gigabytes(files), 1e-9):.0%})")

    for bucket in args.delete or []:
        entries = buckets[bucket]
        freed = gigabytes(entries)
        for path in entries:
            path.unlink()
        print(f"deleted {len(entries)} files from {bucket}, {freed:.2f} GB freed")

    print(f"\nwrote {manifest}\n      {prune}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
