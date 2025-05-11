import tomli  # or import tomllib for Python 3.11+
import hashlib
import sys
from pathlib import Path
from collections import defaultdict


def parse_pylock_toml(path):
    with open(path, "rb") as f:
        data = tomli.load(f)

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


def write_requirements_txt(package_hashes, output_path="requirements.txt"):
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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pylock_to_requirements.py pylock.toml")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)

    pkgs = parse_pylock_toml(path)
    dest = path.parent / (path.stem.replace('pylock','requirement_with_hash')+ '.txt')
    write_requirements_txt(pkgs, dest)
