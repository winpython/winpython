"""Read a cycle TOML and emit its build configuration as GITHUB_OUTPUT lines.

    python .github/scripts/cycle_config.py cycles/2026_04.toml 3.14

Writes to $GITHUB_OUTPUT when set, otherwise stdout, so it can be run locally
to see exactly what a workflow run would get. tomllib is stdlib from 3.11, and
GitHub runners are newer than that, so this needs no dependency.

Everything the build job needs is decided here rather than re-derived per
matrix leg in PowerShell:

  * which flavors this Python can build -- right architecture, and a pylock
    present in the cycle directory. A flavor the cycle declares but has no
    lockfile for costs nothing, so it can stay declared until it comes back.
  * the file names those flavors use, so a leg never has to look one up.
  * a cycle with no lockfiles at all fails here, loudly, instead of starting
    runners whose every step is then skipped.

Paths are relative to the working directory, which in CI is the checkout root.
"""
import json
import os
import sys
import tomllib
from pathlib import Path


def flavor_entry(cfg: dict, flavor: dict, ver2: str, python_version: str) -> dict | None:
    """One matrix leg, or None when this flavor has no lockfile to build.

    Names follow the layout the publish step writes: pylock.64-<ver2 with
    underscores><flavor><release level>.toml, plus the _wheels variants the
    wheelhouse flavor adds.
    """
    cycle_dir = Path(cfg["cycle_dir"])
    level = cfg.get("release_level", "")
    stem = f"64-{ver2.replace('.', '_')}{flavor['name']}{level}"

    lockfile = cycle_dir / f"pylock.{stem}.toml"
    if not lockfile.is_file():
        return None

    def optional(path: Path) -> str:
        return path.as_posix() if path.is_file() else ""

    return {
        "name": flavor["name"],
        "PANDOC": flavor["PANDOC"],
        "formats": flavor["formats"],
        "lockfile": lockfile.as_posix(),
        "lockfile_wheels": optional(cycle_dir / f"pylock.{stem}_wheels.toml"),
        "requirements_wheels": optional(cycle_dir / f"requir.{stem}_wheels.txt"),
        "winpyver": f"{ver2}{flavor['name']}{level}",
        "artifact_name": f"publish_{python_version}{flavor['name']}",
    }


def build_config(cfg: dict, requested: str) -> dict:
    pythons = cfg["pythons"]
    if requested not in pythons:
        raise SystemExit(
            f"no entry for python {requested!r}; this cycle offers {', '.join(sorted(pythons))}"
        )
    entry = pythons[requested]

    # the check the PowerShell version did: ver2's first 3 parts must appear in
    # the tarball URL, so a copy-paste slip between the two cannot go unnoticed
    ver2 = entry["ver2"]
    short = ".".join(ver2.split(".")[:3])
    if short not in entry["src"]:
        raise SystemExit(f"{requested}: '{short}' not found in src {entry['src']}")

    # a trailing F marks the free-threaded build; it is not part of the version
    python_version = requested[:-1] if requested.endswith("F") else requested
    arch = "64F" if requested.endswith("F") else "64"

    flavors = []
    for flavor in cfg["flavors"]:
        if str(flavor.get("WINPYARCHDET", "")) != arch:
            continue
        leg = flavor_entry(cfg, flavor, ver2, python_version)
        if leg is not None:
            flavors.append(leg)
    if not flavors:
        raise SystemExit(
            f"{requested}: no pylock.64-{ver2.replace('.', '_')}<flavor>"
            f"{cfg.get('release_level', '')}.toml under {cfg['cycle_dir']}; "
            "commit the lockfiles for this cycle before dispatching"
        )

    build_location = f"WPy64-{ver2.replace('.', '')}"
    return {
        "ver2": ver2,
        "python_version": python_version,
        "src": entry["src"],
        "sha": entry["sha"],
        "cycle_dir": cfg["cycle_dir"],
        "release_level": cfg.get("release_level", ""),
        "build_location": build_location,
        "destwheelhouse": f"{build_location}\\wheelhouse\\included.wheels",
        "pandoc_source": cfg["pandoc"]["source"],
        "pandoc_sha256": cfg["pandoc"]["sha256"],
        # consumed by the build job as strategy.matrix via fromJSON
        "matrix": json.dumps({"flavor": flavors}, separators=(",", ":")),
    }


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        raise SystemExit(f"usage: {Path(argv[0]).name} <cycle.toml> <python_version>")
    cfg_path = Path(argv[1])
    if not cfg_path.is_file():
        raise SystemExit(f"no such cycle file: {cfg_path}")
    with cfg_path.open("rb") as fh:
        cfg = tomllib.load(fh)

    rendered = "".join(f"{k}={v}\n" for k, v in build_config(cfg, argv[2]).items())
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(rendered)
    sys.stdout.write(rendered)


if __name__ == "__main__":
    main(sys.argv)
