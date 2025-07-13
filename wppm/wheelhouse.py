#!/usr/bin/env python3
"""
WheelHouse.py - manage WinPython local WheelHouse.
"""
import sys
from pathlib import Path
from collections import defaultdict
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple
from . import packagemetadata as pm

# Use tomllib if available (Python 3.11+), otherwise fall back to tomli
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # For older Python versions
    except ImportError:
        print("Please install tomli for Python < 3.11: pip install tomli")
        sys.exit(1)

def parse_pylock_toml(path: Path) -> Dict[str, Dict[str, str | List[str]]]:
    """Parse a pylock.toml file and extract package information."""
    with open(path, "rb") as f:
        data = tomllib.load(f)

    # This dictionary maps package names to (version, [hashes])
    package_hashes = defaultdict(lambda: {"version": "", "hashes": []})

    for entry in data.get("packages", []):
        name = entry["name"]
        version = entry["version"]
        all_hashes = []

        # Handle wheels
        for wheel in entry.get("wheels", []):
            sha256 = wheel.get("hashes", {}).get("sha256")
            if sha256:
                all_hashes.append(sha256)

        # Handle sdist (if present)
        sdist = entry.get("sdist")
        if sdist and "hashes" in sdist:
            sha256 = sdist["hashes"].get("sha256")
            if sha256:
                all_hashes.append(sha256)

        package_hashes[name]["version"] = version
        package_hashes[name]["hashes"].extend(all_hashes)

    return package_hashes

def write_requirements_txt(package_hashes: Dict[str, Dict[str, str | List[str]]], output_path: Path) -> None:
    """Write package requirements to a requirements.txt file."""
    with open(output_path, "w") as f:
        for name, data in sorted(package_hashes.items()):
            version = data["version"]
            hashes = data["hashes"]

            if hashes:
                f.write(f"{name}=={version} \\\n")
                for i, h in enumerate(hashes):
                    end = " \\\n" if i < len(hashes) - 1 else "\n"
                    f.write(f"    --hash=sha256:{h}{end}")
            else:
                f.write(f"{name}=={version}\n")

    print(f"✅ requirements.txt written to {output_path}")

def pylock_to_req(path: Path, output_path: Optional[Path] = None) -> None:
    """Convert a pylock.toml file to requirements.txt."""
    pkgs = parse_pylock_toml(path)
    if not output_path:
        output_path = path.parent / (path.stem.replace('pylock', 'requirement_with_hash') + '.txt')
    write_requirements_txt(pkgs, output_path)

def run_pip_command(command: List[str], check: bool = True, capture_output=True) -> Tuple[bool, Optional[str]]:
    """Run a pip command and return the result."""
    print('\n', ' '.join(command),'\n')
    try:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=True,
            check=check
        )
        return (result.returncode == 0), (result.stderr or result.stdout)
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError:
        return False, "pip or Python not found."
    except Exception as e:
        return False, f"Unexpected error: {e}"

def get_wheels(requirements: Path, wheeldrain: Path, wheelorigin: Optional[Path] = None
               , only_check: bool = True,post_install: bool = False) -> bool:
    """Download or check Python wheels based on requirements."""
    added = []
    if wheelorigin:
        added = ['--no-index', '--trusted-host=None', f'--find-links={wheelorigin}']
    pre_checks = [sys.executable, "-m", "pip", "install", "--dry-run", "--no-deps", "--require-hashes", "-r", str(requirements)] + added
    instruction = [sys.executable, "-m", "pip", "download", "--no-deps", "--require-hashes", "-r", str(requirements), "--dest", str(wheeldrain)] + added
    if wheeldrain:
        added = ['--no-index', '--trusted-host=None', f'--find-links={wheeldrain}']
    post_install_cmd = [sys.executable, "-m", "pip", "install", "--no-deps", "--require-hashes", "-r", str(requirements)] + added

    # Run pip dry-run, only  if a move of wheels
    if  wheelorigin and wheelorigin != wheeldrain:
        success, output = run_pip_command(pre_checks, check=False)
        if not success:
            print("❌ Dry-run failed. Here's the output:\n")
            print(output or "")
            return False

        print("✅ Requirements can be installed successfully (dry-run passed).\n")

    # All ok
    if only_check and not post_install:
        return True

    # Want to install
    if not only_check and post_install:
        success, output = run_pip_command(post_install_cmd, check=False, capture_output=False)
        if not success:
            print("❌ Installation failed. Here's the output:\n")
            print(output or "")
            return False
        return True

    # Otherwise download also, but not install direct
    success, output = run_pip_command(instruction)
    if not success:
        print("❌ Download failed. Here's the output:\n")
        print(output or "")
        return False

    return True

def get_pylock_wheels(wheelhouse: Path, lockfile: Path, wheelorigin: Optional[Path] = None, wheeldrain: Optional[Path] = None) -> None:
    """Get wheels asked pylock file."""
    filename = Path(lockfile).name
    wheelhouse.mkdir(parents=True, exist_ok=True)
    trusted_wheelhouse = wheelhouse / "included.wheels"
    trusted_wheelhouse.mkdir(parents=True, exist_ok=True)

    filename_lock = wheelhouse / filename
    filename_req = wheelhouse / (Path(lockfile).stem.replace('pylock', 'requirement') + '.txt')

    pylock_to_req(Path(lockfile), filename_req)

    if not str(Path(lockfile)) == str(filename_lock):
        shutil.copy2(lockfile, filename_lock)

    # We create a destination for wheels that is specific, so we can check all is there
    destination_wheelhouse = Path(wheeldrain) if wheeldrain else wheelhouse / Path(lockfile).name.replace('.toml', '.wheels')
    destination_wheelhouse.mkdir(parents=True, exist_ok=True)
    # there can be an override

    in_trusted = False

    if wheelorigin is None:
        # Try from trusted WheelHouse
        print(f"\n\n*** Checking if we can install from our Local WheelHouse: ***\n    {trusted_wheelhouse}\n\n")
        in_trusted = get_wheels(filename_req, destination_wheelhouse, wheelorigin=trusted_wheelhouse, only_check=True)
        if in_trusted:
            print(f"\n\n***  We can install from Local WheelHouse: ***\n    {trusted_wheelhouse}\n\n")
            in_installed = get_wheels(filename_req, trusted_wheelhouse, wheelorigin=trusted_wheelhouse, only_check=False, post_install=True)

    if not in_trusted:
        post_install = True if wheelorigin and Path(wheelorigin).is_dir and Path(wheelorigin).samefile(destination_wheelhouse) else False
        if post_install:
            print(f"\n\n*** Installing from Local WheelHouse: ***\n    {destination_wheelhouse}\n\n")
        else:
            print(f"\n\n*** Re-Checking if we can install from: {'pypi.org' if not wheelorigin or wheelorigin == '' else wheelorigin}\n\n")

        in_pylock = get_wheels(filename_req, destination_wheelhouse, wheelorigin=wheelorigin, only_check=False, post_install=post_install)
        if in_pylock:
            if not post_install:
                print(f"\n\n*** You can now install from this dedicated WheelHouse: ***\n    {destination_wheelhouse}")
                print(f"\n via:\n    wppm {filename_lock} -wh {destination_wheelhouse}\n")
        else:
            print(f"\n\n*** We can't install {filename} ! ***\n\n")

def list_packages_with_metadata(directory: str) -> List[Tuple[str, str, str]]:
    "get metadata from a Wheelhouse directory"
    packages = pm.get_directory_metadata(directory)
    results = [ (p.name, p.version, p.summary) for p in packages]
    return results

def main() -> None:
    """Main entry point for the script."""
    if len(sys.argv) != 2:
        print("Usage: python pylock_to_requirements.py pylock.toml")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)

    pkgs = parse_pylock_toml(path)
    dest = path.parent / (path.stem.replace('pylock', 'requirement_with_hash') + '.txt')
    write_requirements_txt(pkgs, dest)

if __name__ == "__main__":
    main()
