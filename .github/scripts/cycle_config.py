"""Read a cycle TOML and emit its build configuration as GITHUB_OUTPUT lines.

    python .github/scripts/cycle_config.py cycles/2026_03.toml 3.14

Writes to $GITHUB_OUTPUT when set, otherwise stdout, so it can be run locally
to see exactly what a workflow run would get. tomllib is stdlib from 3.11, and
GitHub runners are newer than that, so this needs no dependency.
"""
import json
import os
import sys
import tomllib
from pathlib import Path


def build_config(cfg: dict, requested: str) -> dict:
    pythons = cfg["pythons"]
    if requested not in pythons:
        raise SystemExit(
            f"no entry for python {requested!r}; this cycle offers {', '.join(sorted(pythons))}"
        )
    entry = pythons[requested]

    # the check the PowerShell version did: ver2's first 3 parts must appear in
    # the tarball URL, so a copy-paste slip between the two cannot go unnoticed
    short = ".".join(entry["ver2"].split(".")[:3])
    if short not in entry["src"]:
        raise SystemExit(f"{requested}: '{short}' not found in src {entry['src']}")

    return {
        "ver2": entry["ver2"],
        "src": entry["src"],
        "sha": entry["sha"],
        "cycle_dir": cfg["cycle_dir"],
        "release_level": cfg.get("release_level", ""),
        "pandoc_source": cfg["pandoc"]["source"],
        "pandoc_sha256": cfg["pandoc"]["sha256"],
        # consumed by the build job as strategy.matrix via fromJSON
        "matrix": json.dumps({"flavor": cfg["flavors"]}, separators=(",", ":")),
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
