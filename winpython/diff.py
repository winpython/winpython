# -*- coding: utf-8 -*-
#
# WinPython diff.py script (streamlined, with historical and flexible modes)
# Copyright © 2013 Pierre Raybaut
# Copyright © 2014-2025+ The Winpython development team https://github.com/winpython/
# Licensed under the terms of the MIT License

import os
import re
import sys
import shutil
from pathlib import Path
from packaging import version
from . import utils

CHANGELOGS_DIR = Path(__file__).parent.parent / "changelogs"

class Package:
    PATTERNS = [
        r"\[([\w\-\:\/\.\_]+)\]\(([^)]+)\) \| ([^\|]*) \| ([^\|]*)",  # SourceForge
        r"\[([\w\-\:\/\.\_]+) ([^\]\ ]+)\] \| ([^\|]*) \| ([^\|]*)"   # Google Code
    ]
    def __init__(self, text=None):
        self.name = self.url = self.version = self.description = None
        if text:
            self.from_text(text)
    def from_text(self, text):
        for pattern in self.PATTERNS:
            match = re.match(pattern, text)
            if match:
                self.name, self.url, self.version, self.description = match.groups()
                return
        raise ValueError(f"Unrecognized package line format: {text}")

class PackageIndex:
    HEADERS = {"tools": "### Tools", "python": "### Python packages", "wheelhouse": "### WheelHouse packages"}
    BLANKS = ["Name | Version | Description", "-----|---------|------------", "", "<details>", "</details>"]

    def __init__(self, content):
        self.packages = {k: {} for k in self.HEADERS}
        self._parse_index(content)

    def _parse_index(self, text):
        current = None
        for line in text.splitlines():
            if line in self.HEADERS.values():
                current = [k for k, v in self.HEADERS.items() if v == line][0]
                continue
            if line.strip() in self.BLANKS:
                continue
            if current:
                try:
                    pkg = Package(line)
                    self.packages[current][pkg.name] = pkg
                except Exception:
                    continue

def compare_packages(old, new):
    def normalize(d): return {k.replace("-", "_").lower(): v for k, v in d.items()}
    old, new = normalize(old), normalize(new)
    added = [new[k] for k in new if k not in old]
    upgraded = [new[k] for k in new if k in old and new[k].version != old[k].version]
    removed = [old[k] for k in old if k not in new]
    output = ""
    if added:
        output += "\nNew packages:\n" + "".join(f"  * {p.name} {p.version} ({p.description})\n" for p in added)
    if upgraded:
        output += "\nUpgraded packages:\n" + "".join(f"  * {p.name} {old[p.name].version} → {p.version} ({p.description})\n" for p in upgraded if p.name in old)
    if removed:
        output += "\nRemoved packages:\n" + "".join(f"  * {p.name} {p.version} ({p.description})\n" for p in removed)
    return output or "\nNo differences found.\n"

def compare_markdown_sections(md1, md2, header1="python", header2="python", label1="Input1", label2="Input2"):
    pkgs1 = PackageIndex(md1).packages
    pkgs2 = PackageIndex(md2).packages
    diff = compare_packages(pkgs1[header1], pkgs2[header2])
    # If comparing the same section, use the historical header
    if header1 == header2 and header1 in PackageIndex.HEADERS:
        title = PackageIndex.HEADERS[header1]
    else:
        title = f"## {label1} [{header1}] vs {label2} [{header2}]"
    return f"{title}\n\n{diff}" 

def compare_markdown_section_pairs(md1, md2, header_pairs, label1="Input1", label2="Input2"):
    pkgs1 = PackageIndex(md1).packages
    pkgs2 = PackageIndex(md2).packages
    text = f"# {label1} vs {label2} section-pairs comparison\n"
    for h1, h2 in header_pairs:
        diff = compare_packages(pkgs1[h1], pkgs2[h2])
        if diff.strip() and diff != "No differences found.\n":
            text += f"\n## {label1} [{h1}] vs {label2} [{h2}]\n\n{diff}\n"
    return text

def compare_files(file1, file2, mode="full", header1=None, header2=None, header_pairs=None):
    with open(file1, encoding=utils.guess_encoding(file1)[0]) as f1, \
         open(file2, encoding=utils.guess_encoding(file2)[0]) as f2:
        md1, md2 = f1.read(), f2.read()
    if mode == "full":
        result = ""
        for k in PackageIndex.HEADERS:
            result += compare_markdown_sections(md1, md2, k, k, file1, file2) + "\n"
        return result
    elif mode == "section":
        return compare_markdown_sections(md1, md2, header1, header2, file1, file2)
    elif mode == "pairs":
        return compare_markdown_section_pairs(md1, md2, header_pairs, file1, file2)
    else:
        raise ValueError("Unknown mode.")

# --- ORIGINAL/HISTORICAL VERSION-TO-VERSION COMPARISON ---

def find_previous_version(target_version, searchdir=None, flavor="", architecture=64):
    search_dir = Path(searchdir) if searchdir else CHANGELOGS_DIR
    pattern = re.compile(rf"WinPython{flavor}-{architecture}bit-([0-9\.]+)\.(txt|md)")
    versions = [pattern.match(f).group(1) for f in os.listdir(search_dir) if pattern.match(f)]
    versions = [v for v in versions if version.parse(v) < version.parse(target_version)]
    return max(versions, key=version.parse, default=target_version)

def load_version_markdown(version, searchdir, flavor="", architecture=64):
    filename = Path(searchdir) / f"WinPython{flavor}-{architecture}bit-{version}.md"
    if not filename.exists():
        raise FileNotFoundError(f"Changelog not found: {filename}")
    with open(filename, "r", encoding=utils.guess_encoding(filename)[0]) as f:
        return f.read()

def compare_package_indexes(version2, version1=None, searchdir=None, flavor="", flavor1=None, architecture=64):
    searchdir = Path(searchdir) if searchdir else CHANGELOGS_DIR
    version1 = version1 or find_previous_version(version2, searchdir, flavor, architecture)
    flavor1 = flavor1 or flavor
    md1 = load_version_markdown(version1, searchdir, flavor1, architecture)
    md2 = load_version_markdown(version2, searchdir, flavor, architecture)
    result = f"# WinPython {architecture}bit {version2}{flavor} vs {version1}{flavor1}\n"
    result = (
        f"## History of changes for WinPython-{architecture}bit {version2 + flavor}\r\n\r\n"
        f"The following changes were made to WinPython-{architecture}bit distribution since version {version1 + flavor1}.\n\n\n"
        "<details>\n\n"
    )
    for k in PackageIndex.HEADERS:
        result += compare_markdown_sections(md1, md2, k, k, version1, version2) + "\n"
    return result+ "\n</details>\n\n* * *\n"

def copy_changelogs(version, searchdir, flavor="", architecture=64, basedir=None):
    """Copy all changelogs for a major.minor version into basedir."""
    basever = ".".join(str(version).split(".")[:2])
    pattern = re.compile(rf"WinPython{flavor}-{architecture}bit-{basever}[0-9\.]*\.(txt|md)")
    dest = Path(basedir)
    for fname in os.listdir(searchdir):
        if pattern.match(fname):
            shutil.copyfile(Path(searchdir) / fname, dest / fname)

def write_changelog(version2, version1=None, searchdir=None, flavor="", architecture=64, basedir=None):
    """Write changelog between version1 and version2 of WinPython."""
    searchdir = Path(searchdir) if searchdir else CHANGELOGS_DIR
    if basedir:
        copy_changelogs(version2, searchdir, flavor, architecture, basedir)
    changelog = compare_package_indexes(version2, version1, searchdir, flavor, architecture=architecture)
    output_file = searchdir / f"WinPython{flavor}-{architecture}bit-{version2}_History.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(changelog)
    if basedir:
        shutil.copyfile(output_file, Path(basedir) / output_file.name)

def print_usage():
    print("Usage:")
    print("  python diff.py file1.md file2.md")
    print("    - Compare all sections of two markdown files.")
    print("  python diff.py file1.md file2.md --section header1 header2")
    print("    - Compare section 'header1' of file1 with section 'header2' of file2.")
    print("  python diff.py file1.md file2.md --pairs header1a header2a [header1b header2b ...]")
    print("    - Compare pairs of sections. Example: python diff.py f1.md f2.md --pairs python wheelhouse tools tools")
    print("  python diff.py <version2> <version1> [searchdir] [flavor] [architecture]")
    print("    - Compare WinPython markdown changelogs by version (historical mode).")
    print("  python diff.py --write-changelog <version2> <version1> [searchdir] [flavor] [architecture] [basedir]")
    print("    - Write changelog between version1 and version2 to file (and optionally copy to basedir).")

if __name__ == "__main__":
    args = sys.argv
    if len(args) >= 3 and all(arg.lower().endswith('.md') for arg in args[1:3]):
        file1, file2 = args[1], args[2]
        if len(args) == 3:
            print(compare_files(file1, file2))
        elif args[3] == "--section" and len(args) >= 6:
            h1, h2 = args[4], args[5]
            print(compare_files(file1, file2, mode="section", header1=h1, header2=h2))
        elif args[3] == "--pairs" and len(args) > 4 and len(args[4:]) % 2 == 0:
            pairs = list(zip(args[4::2], args[5::2]))
            print(compare_files(file1, file2, mode="pairs", header_pairs=pairs))
        else:
            print_usage()
    elif len(args) >= 2 and args[1] == "--write-changelog":
        # Usage: --write-changelog <version2> <version1> [searchdir] [flavor] [architecture] [basedir]
        if len(args) < 4:
            print_usage()
            sys.exit(1)
        version2 = args[2]
        version1 = args[3]
        searchdir = args[4] if len(args) > 4 else CHANGELOGS_DIR
        flavor = args[5] if len(args) > 5 else ""
        architecture = int(args[6]) if len(args) > 6 else 64
        basedir = args[7] if len(args) > 7 else None
        write_changelog(version2, version1, searchdir, flavor, architecture, basedir)
        print(f"Changelog written for {version2} vs {version1}.")
    elif len(args) >= 3:
        version2 = args[1]
        version1 = args[2] if len(args) > 2 and not args[2].endswith('.md') else None
        searchdir = args[3] if len(args) > 3 else CHANGELOGS_DIR
        flavor = args[4] if len(args) > 4 else ""
        architecture = int(args[5]) if len(args) > 5 else 64
        print(compare_package_indexes(version2, version1, searchdir, flavor, architecture=architecture))
    else:
        print_usage()