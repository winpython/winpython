"""Read a cycle TOML and emit its build configuration as GITHUB_OUTPUT lines.

    python .github/scripts/cycle_config.py cycles/2026_04.toml all
    python .github/scripts/cycle_config.py cycles/2026_04.toml 3.14
    python .github/scripts/cycle_config.py cycles/2026_04.toml all slim,slimf

Writes to $GITHUB_OUTPUT when set, otherwise stdout, so it can be run locally
to see exactly what a workflow run would get. tomllib is stdlib from 3.11, and
GitHub runners are newer than that, so this needs no dependency.

Everything the build job needs is decided here rather than re-derived per
matrix leg in PowerShell:

  * which (python, flavor) pairs this cycle can build -- right architecture,
    and a pylock present in the cycle directory. A flavor the cycle declares
    but has no lockfile for costs nothing, so it can stay declared until it
    comes back, and "all" skips a Python whose lockfiles are not committed yet
    rather than failing the cycle over it.
  * the version, tarball and paths each pair needs, carried by the leg itself.
    A leg naming its own Python is what lets "all" build the whole cycle in one
    dispatch instead of one per Python version.
  * the tag its release goes under. Derived from the cycle name and release
    level -- 2026_04 at level b1 publishes under "2026-04b1" -- so a respin is
    a level bump rather than a tag to invent. A cycle wanting some other tag
    says so with a release_tag key.
  * a cycle with nothing to build fails here, loudly, instead of starting
    runners whose every step is then skipped.
  * a flavor's optional post suffix ("_post1"): a rebuild of the same
    lockfile under new file names. It can join a release that is already
    published, since nothing there gets replaced.

Paths are relative to the working directory, which in CI is the checkout root.
"""
import datetime
import json
import os
import sys
import tomllib
from pathlib import Path

# git refuses these in a ref name; catching them here beats failing at upload
# time, an hour into a build. Not the whole of git-check-ref-format, just the
# parts a hand-written tag realistically trips over.
TAG_FORBIDDEN = set(" ~^:?*[\\\x7f") | {chr(c) for c in range(32)}

# a post suffix lands in file names and URLs
POST_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")


def python_facts(requested: str, entry: dict) -> dict:
    """What every flavor of one Python shares.

    A trailing F marks the free-threaded build: it picks a different tarball
    and a different set of flavors, but it is not part of the version number.
    """
    ver2 = entry["ver2"]

    # the check the PowerShell version did: ver2's first 3 parts must appear in
    # the tarball URL, so a copy-paste slip between the two cannot go unnoticed
    short = ".".join(ver2.split(".")[:3])
    if short not in entry["src"]:
        raise SystemExit(f"{requested}: '{short}' not found in src {entry['src']}")

    build_location = f"WPy64-{ver2.replace('.', '')}"
    return {
        "python_versionf": requested,
        "python_version": requested[:-1] if requested.endswith("F") else requested,
        "archdet": "64F" if requested.endswith("F") else "64",
        "ver2": ver2,
        "src": entry["src"],
        "sha": entry["sha"],
        "build_location": build_location,
        "destwheelhouse": rf"{build_location}\wheelhouse\included.wheels",
    }


def flavor_entry(cfg: dict, flavor: dict, python: dict) -> dict | None:
    """One matrix leg, or None when this flavor has no lockfile to build.

    Names follow the layout the publish step writes: pylock.64-<ver2 with
    underscores><flavor><release level>.toml, plus the _wheels variants the
    wheelhouse flavor adds.
    """
    cycle_dir = Path(cfg["cycle_dir"])
    level = cfg.get("release_level", "")
    stem = f"64-{python['ver2'].replace('.', '_')}{flavor['name']}{level}"

    lockfile = cycle_dir / f"pylock.{stem}.toml"
    if not lockfile.is_file():
        return None

    def optional(path: Path) -> str:
        return path.as_posix() if path.is_file() else ""

    post = flavor.get("post", "")
    if set(post) - POST_ALLOWED:
        raise SystemExit(f"{flavor['name']}: post {post!r} must be letters, digits, '.', '_' or '-'")

    leg = {key: value for key, value in python.items() if key != "archdet"}
    leg.update(
        name=flavor["name"],
        PANDOC=flavor["PANDOC"],
        formats=flavor["formats"],
        lockfile=lockfile.as_posix(),
        lockfile_wheels=optional(cycle_dir / f"pylock.{stem}_wheels.toml"),
        requirements_wheels=optional(cycle_dir / f"requir.{stem}_wheels.txt"),
        post=post,
        winpyver=f"{python['ver2']}{flavor['name']}{level}{post}",
        artifact_name=f"publish_{python['python_version']}{flavor['name']}",
    )
    return leg


def legs_for(cfg: dict, requested: str) -> list[dict]:
    """Every buildable (flavor) leg of one Python of this cycle."""
    python = python_facts(requested, cfg["pythons"][requested])
    found = []
    for flavor in cfg["flavors"]:
        if str(flavor.get("WINPYARCHDET", "")) != python["archdet"]:
            continue
        leg = flavor_entry(cfg, flavor, python)
        if leg is not None:
            found.append(leg)
    return found


def release_tag(cfg: dict, cycle_name: str) -> str:
    """The tag this cycle's release goes under.

    "2026_04" at release level "b1" gives "2026-04b1", the name the cycle goes
    by in public. No date in it on purpose: a tag has to stay put so that
    re-running one missing flavor lands on the release the others are already
    on, and so that the download URLs the site publishes keep resolving. A
    second build of the same cycle is a release_level bump, which says more
    than a date would.
    """
    tag = cfg.get("release_tag") or f"{cycle_name.replace('_', '-')}{cfg.get('release_level', '')}"
    bad = sorted(TAG_FORBIDDEN.intersection(tag))
    if bad or ".." in tag or tag.startswith("/") or tag.endswith(("/", ".", ".lock")):
        raise SystemExit(f"release tag {tag!r} is not a usable git ref name")
    return tag


def ordinal(day: int) -> str:
    """1st, 2nd, 3rd, 4th ... and the 11th/12th/13th exceptions."""
    if 11 <= day % 100 <= 13:
        return f"{day}th"
    return f"{day}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th') }"


def release_title(cfg: dict, cycle_name: str, today: datetime.date | None = None) -> str:
    """"WinPython 2026-04 b1 of September 6th 2026", the shape releases have used.

    Kept deliberately close to the titles written by hand before this: cycle,
    then the level after a space -- the tag runs them together, the title does
    not -- then the date, no comma, which is how all but one of them read.

    The date is the day the draft is opened, since that is the only day the
    build knows about. A cycle publishing much later than it was built can
    still have the title edited; the tag, which is what URLs are built on,
    does not move.
    """
    today = today or datetime.date.today()
    level = cfg.get("release_level", "")
    name = f"{cycle_name.replace('_', '-')} {level}".strip()
    return f"WinPython {name} of {today:%B} {ordinal(today.day)} {today.year}"


def wanted_flavors(cfg: dict, flavors: str) -> set[str] | None:
    """The flavor names a comma-separated input asks for; None means all.

    A typo would otherwise filter everything out, or quietly build less than
    asked, so a name the cycle does not declare is refused.
    """
    if flavors.strip() in ("", "all"):
        return None
    names = {name.strip() for name in flavors.split(",") if name.strip()}
    declared = {flavor["name"] for flavor in cfg["flavors"]}
    unknown = names - declared
    if unknown:
        raise SystemExit(
            f"unknown flavor {', '.join(sorted(unknown))}; this cycle declares "
            f"{', '.join(sorted(declared))} (or 'all')"
        )
    return names


def build_config(cfg: dict, requested: str, cycle_name: str, flavors: str = "all") -> dict:
    pythons = cfg["pythons"]
    only = wanted_flavors(cfg, flavors)
    if requested == "all":
        wanted = list(pythons)
    elif requested in pythons:
        wanted = [requested]
    else:
        raise SystemExit(
            f"no entry for python {requested!r}; this cycle offers "
            f"{', '.join(sorted(pythons))} (or 'all')"
        )

    legs = [leg for python in wanted for leg in legs_for(cfg, python)]
    if only is not None:
        legs = [leg for leg in legs if leg["name"] in only]
    if not legs and only is not None:
        raise SystemExit(f"{requested}: none of {flavors} can be built for this Python")
    if not legs:
        missing = ", ".join(
            f"pylock.64-{pythons[p]['ver2'].replace('.', '_')}<flavor>"
            f"{cfg.get('release_level', '')}.toml"
            for p in wanted
        )
        raise SystemExit(
            f"{requested}: no {missing} under {cfg['cycle_dir']}; "
            "commit the lockfiles for this cycle before dispatching"
        )

    return {
        "cycle_dir": cfg["cycle_dir"],
        "release_level": cfg.get("release_level", ""),
        "release_tag": release_tag(cfg, cycle_name),
        "release_title": release_title(cfg, cycle_name),
        # every leg renamed by a post suffix: none of its files can replace one
        "adds_only": "true" if all(leg["post"] for leg in legs) else "false",
        "pandoc_source": cfg["pandoc"]["source"],
        "pandoc_sha256": cfg["pandoc"]["sha256"],
        # consumed by the build job as strategy.matrix via fromJSON
        "matrix": json.dumps({"leg": legs}, separators=(",", ":")),
    }


def main(argv: list[str]) -> None:
    if len(argv) not in (3, 4):
        raise SystemExit(f"usage: {Path(argv[0]).name} <cycle.toml> <python_version|all> [flavors|all]")
    cfg_path = Path(argv[1])
    if not cfg_path.is_file():
        raise SystemExit(f"no such cycle file: {cfg_path}")
    with cfg_path.open("rb") as fh:
        cfg = tomllib.load(fh)

    config = build_config(cfg, argv[2], cfg_path.stem, argv[3] if len(argv) == 4 else "all")
    rendered = "".join(f"{k}={v}\n" for k, v in config.items())
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(rendered)
    sys.stdout.write(rendered)


if __name__ == "__main__":
    main(sys.argv)
