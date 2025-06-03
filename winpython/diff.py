# -*- coding: utf-8 -*-
#
# WinPython diff.py script
# Copyright © 2013 Pierre Raybaut
# Copyright © 2014-2025+ The Winpython development team https://github.com/winpython/
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

import os
from pathlib import Path
import re
import shutil
from packaging import version
from . import utils

CHANGELOGS_DIR = Path(__file__).parent.parent / "changelogs"
assert CHANGELOGS_DIR.is_dir()

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

    def to_wiki(self):
        return f"  * [{self.name}]({self.url}) {self.version} ({self.description})\n"

    def upgrade_wiki(self, other):
        return f"  * [{self.name}]({self.url}) {other.version} → {self.version} ({self.description})\n"

class PackageIndex:
    HEADERS = {"tools": "### Tools", "python": "### Python packages", "wheelhouse": "### WheelHouse packages"}
    BLANKS = ["Name | Version | Description", "-----|---------|------------", "", "<details>", "</details>"]

    def __init__(self, version, searchdir=None, flavor="", architecture=64):
        self.version = version
        self.flavor = flavor
        self.searchdir = searchdir
        self.architecture = architecture
        self.packages = {"tools": {}, "python": {}, "wheelhouse": {}}
        self._load_index()

    def _load_index(self):
        filename = self.searchdir / f"WinPython{self.flavor}-{self.architecture}bit-{self.version}.md"
        if not filename.exists():
            raise FileNotFoundError(f"Changelog not found: {filename}")

        with open(filename, "r", encoding=utils.guess_encoding(filename)[0]) as f:
            self._parse_index(f.read())

    def _parse_index(self, text):
        current = None
        for line in text.splitlines():
            if line in self.HEADERS.values():
                current = [k for k, v in self.HEADERS.items() if v == line][0]
                continue
            if line.strip() in self.BLANKS:
                continue
            if current:
                pkg = Package(line)
                self.packages[current][pkg.name] = pkg

def compare_packages(old, new):
    """Return difference between package old and package new"""

    # wheel replace '-' per '_' in key
    def normalize(d): return {k.replace("-", "_").lower(): v for k, v in d.items()}
    old, new = normalize(old), normalize(new)
    output = ""

    added = [new[k].to_wiki() for k in new if k not in old]
    upgraded = [new[k].upgrade_wiki(old[k]) for k in new if k in old and new[k].version != old[k].version]
    removed = [old[k].to_wiki() for k in old if k not in new]

    if added:
        output += "New packages:\n\n" + "".join(added) + "\n\n"
    if upgraded:
        output += "Upgraded packages:\n\n" + "".join(upgraded) + "\n\n"
    if removed:
        output += "Removed packages:\n\n" + "".join(removed) + "\n\n"
    return output

def find_previous_version(target_version, searchdir=None, flavor="", architecture=64):
    """Find version which is the closest to `version`"""
    search_dir = Path(searchdir) if searchdir else CHANGELOGS_DIR
    pattern = re.compile(rf"WinPython{flavor}-{architecture}bit-([0-9\.]+)\.(txt|md)")
    versions = [pattern.match(f).group(1) for f in os.listdir(search_dir) if pattern.match(f)]
    versions = [v for v in versions if version.parse(v) < version.parse(target_version)]
    return max(versions, key=version.parse, default=target_version)

def compare_package_indexes(version2, version1=None, searchdir=None, flavor="", flavor1=None, architecture=64):
    version1 = version1 or find_previous_version(version2, searchdir, flavor, architecture)
    flavor1 = flavor1 or flavor

    pi1 = PackageIndex(version1, searchdir, flavor1, architecture)
    pi2 = PackageIndex(version2, searchdir, flavor, architecture)

    text = (
        f"## History of changes for WinPython-{architecture}bit {version2 + flavor}\r\n\r\n"
        f"The following changes were made to WinPython-{architecture}bit distribution since version {version1 + flavor1}.\n\n\n"
        "<details>\n\n"
    )

    for key in PackageIndex.HEADERS:
        diff = compare_packages(pi1.packages[key], pi2.packages[key])
        if diff:
            text += f"\n{PackageIndex.HEADERS[key]}\n\n{diff}"

    return text + "\n</details>\n\n* * *\n"

def copy_changelogs(version, searchdir, flavor="", architecture=64, basedir=None):
    basever = ".".join(version.split(".")[:2])
    pattern = re.compile(rf"WinPython{flavor}-{architecture}bit-{basever}[0-9\.]*\.(txt|md)")
    dest = Path(basedir)
    for fname in os.listdir(searchdir):
        if pattern.match(fname):
            shutil.copyfile(searchdir / fname, dest / fname)

def write_changelog(version2, version1=None, searchdir=None, flavor="", architecture=64, basedir=None):
    """Write changelog between version1 and version2 of WinPython"""
    if basedir:
        copy_changelogs(version2, searchdir, flavor, architecture, basedir)
    print("comparing_package_indexes", version2, searchdir, flavor, architecture)
    changelog = compare_package_indexes(version2, version1, searchdir, flavor, architecture=architecture)
    output_file = searchdir / f"WinPython{flavor}-{architecture}bit-{version2}_History.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(changelog)
    # Copy to winpython/changelogs back to basedir
    if basedir:
        shutil.copyfile(output_file, basedir / output_file.name)

if __name__ == "__main__":
    print(compare_package_indexes("3.7.4.0", "3.7.2.0", r"C:\WinP\bd37\budot", "Zero", architecture=32))
    write_changelog("3.7.4.0", "3.7.2.0", r"C:\WinP\bd37\budot", "Ps2", architecture=64)
