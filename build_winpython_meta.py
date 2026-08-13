# build_winpython_meta.py
# Local builds are made with Python 3.11 or later.
import os
import sys
import tomllib  # stdlib since 3.11; we choose toml over yaml, more python standard
import subprocess
from pathlib import Path

# Flavor paths are names, not full paths: these say what they hang from.
UNDER_BASEDIR = ("requirements", "source_dirs", "wheelhousereq")
UNDER_ROOT = ("toolsdirs",)

def load_builds(config_file):
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
    python_versions = config.get("pythons", {})
    # A file may still spell out one [[builds]] block per build; otherwise the
    # builds are the (python, flavor) pairs [pythons] asks for.
    builds = config["builds"] if "builds" in config else expand_builds(config)
    return builds, python_versions

def expand_builds(config):
    """One build per flavor listed by each [pythons."3XX"], paths derived.

    A flavor names its files relative to the build directory, so a new Python
    minor is one [pythons] block. Where a Python needs its own file - a
    requirements list under another name, say - [pythons."3XX".overrides.flavor]
    replaces that flavor's entries for that Python alone.
    """
    defaults = config.get("defaults", {})
    flavors = config.get("flavors", {})
    builds = []
    for target, vinfo in config.get("pythons", {}).items():
        root = Path(vinfo.get("root_dir_for_builds", defaults.get("root_dir_for_builds", "")))
        basedir = root / f"bd{target}"
        overrides = vinfo.get("overrides", {})
        for flavor in vinfo.get("builds", []):
            if flavor not in flavors:
                raise KeyError(f"python {target} builds {flavor!r}, which has no [flavors.{flavor}]")
            build = {**defaults, "name": flavor, "python_target": target, "flavor": flavor}
            for key, value in {**flavors[flavor], **overrides.get(flavor, {})}.items():
                if key in UNDER_BASEDIR:
                    value = str(basedir / value)
                elif key in UNDER_ROOT:
                    value = str(root / value)
                build[key] = value
            builds.append(build)
    return builds

def select_builds(builds, wanted):
    """Builds asked for on the command line: "315", "315:slim", ":slim"."""
    if not wanted:
        return builds
    kept = []
    for spec in wanted:
        target, _, flavor = spec.partition(":")
        matching = [b for b in builds
                    if (not target or b["python_target"] == target)
                    and (not flavor or b["flavor"] == flavor)]
        if not matching:
            raise SystemExit(f"no build matches {spec!r}")
        kept += [b for b in matching if b not in kept]
    return kept

def must_exist(path, build, key):
    """pip_install() skips a missing requirements file without failing, which
    would drop those packages silently. Say so instead."""
    if path and not Path(path).exists():
        raise FileNotFoundError(f"build {build['name']!r} needs {key} = {path!r}, which does not exist")
    return path

def declared_file(build, key, default):
    """Path named by the build for `key`, else `default`."""
    declared = build.get(key)
    return str(default) if declared is None else must_exist(str(declared), build, key)

def run_build(build, python_versions, dry_run=False):
    print(f"\n=== Building WinPython: {build['python_target']} {build['name']} ===")
    print(build)

    root_dir_for_builds = build["root_dir_for_builds"]
    my_python_target = build["python_target"]
    my_flavor = build["flavor"]
    my_arch = str(build["arch"])
    my_create_installer = build.get("create_installer", "True")
    my_requirements = must_exist(build.get("requirements", ""), build, "requirements")
    my_source_dirs = build.get("source_dirs", "")
    my_find_links = build.get("find_links", "")
    my_toolsdirs = build.get("toolsdirs", "")
    wheelhousereq = must_exist(build.get("wheelhousereq", ""), build, "wheelhousereq")
    # "pip" (default, what ships) | "none" | "parallel" | "parallel-N"
    my_bytecode = build.get("bytecode", "pip")

    # Get Python release info from TOML [pythons]
    py_target = my_python_target
    vinfo = python_versions.get(py_target, {})
    my_python_target_release = vinfo.get("python_target_release", "")
    my_release = vinfo.get("release", "")
    my_release_level = vinfo.get("my_release_level", "b0")
    # A build may name its own file for a specific problem; otherwise the one
    # shipped beside this script is used.
    here = Path(__file__).parent
    mandatory_requirements = declared_file(build, "mandatory_requirements", here / "mandatory_requirements.txt")
    my_constraints = declared_file(build, "constraints", here / "constraints.txt")

    # Build directory logic
    my_basedir = f"{root_dir_for_builds}\\bd{my_python_target}"
    my_WINPYDIRBASE = f"{my_basedir}\\bu{my_flavor}\\WPy{my_arch}-{my_python_target_release}{my_release}{my_release_level}"

    # Build env paths (customize as needed) already defined per the launcher of that script...
 
    my_python_exe = Path(sys.executable)
    my_buildenvi = str(my_python_exe.parent)

    my_archive_dir = os.path.join(os.getcwd(), "WinPython_build_logs")
    os.makedirs(my_archive_dir, exist_ok=True)

    # Build command
    build_cmd = [
        str(my_python_exe),
        "-m", "winpython.build_winpython",
        "--buildenv", my_buildenvi,
        "--python-target", my_python_target,
        "--release", my_release,
        "--release-level", my_release_level,
        "--winpydirbase", my_WINPYDIRBASE,
        "--flavor", my_flavor,
        "--source_dirs", my_source_dirs,
        "--tools_dirs", my_toolsdirs,
        "--log-dir", my_archive_dir,
        "--mandatory-req", mandatory_requirements,
        "--requirements", my_requirements,
        "--constraints", my_constraints,
        "--find-links", my_find_links,
        "--wheelhousereq", wheelhousereq,
        "--bytecode", my_bytecode,
        "--create-installer", my_create_installer,
    ]

    print("Dry run, build command:" if dry_run else "Running build command:")
    print(" ".join(build_cmd))
    if not dry_run:
        subprocess.run(build_cmd, check=False)

def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = len(args) != len(sys.argv) - 1
    config_file = args[0] if args else "winpython_builds.toml"
    builds, python_versions = load_builds(config_file)
    for build in select_builds(builds, args[1:]):
        run_build(build, python_versions, dry_run)

if __name__ == "__main__":
    main()
