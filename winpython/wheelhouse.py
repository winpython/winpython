#
# WheelHouse.py 
import sys
from pathlib import Path
from collections import defaultdict

# Use tomllib if available (Python 3.11+), otherwise fall back to tomli
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # For older Python versions
    except ImportError:
        print("Please install tomli for Python < 3.11: pip install tomli")
        sys.exit(1)



def parse_pylock_toml(path):
    with open(Path(path), "rb") as f:
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


def write_requirements_txt(package_hashes, output_path="requirements.txt"):
    with open(Path(output_path), "w") as f:
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

def pylock_to_req(path, output_path=None):
    pkgs = parse_pylock_toml(path)
    if not output_path:
        output_path = path.parent / (path.stem.replace('pylock','requirement_with_hash')+ '.txt')
    write_requirements_txt(pkgs, output_path)

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
