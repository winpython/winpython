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
from winpython import utils

CHANGELOGS_DIR = Path(__file__).parent / "changelogs"
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
        return f"  * [{self.name}]({self.url}) {self.version} ({self.description})\r\n"

    def upgrade_wiki(self, other):
        return f"  * [{self.name}]({self.url}) {other.version} → {self.version} ({self.description})\r\n"

class PackageIndex:
    HEADERS = {"tools": "### Tools", "python": "### Python packages", "wheelhouse": "### WheelHouse packages"}
    BLANKS = ["Name | Version | Description", "-----|---------|------------", "", "<details>", "</details>"]

    def __init__(self, version, basedir=None, flavor="", architecture=64):
        self.version = version
        self.flavor = flavor
        self.basedir = basedir
        self.architecture = architecture
        self.packages = {"tools": {}, "python": {}, "wheelhouse": {}}
        self._load_index()

    def _load_index(self):
        filename = CHANGELOGS_DIR / f"WinPython{self.flavor}-{self.architecture}bit-{self.version}.md"
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
        output += "New packages:\r\n\r\n" + "".join(added) + "\r\n"
    if upgraded:
        output += "Upgraded packages:\r\n\r\n" + "".join(upgraded) + "\r\n"
    if removed:
        output += "Removed packages:\r\n\r\n" + "".join(removed) + "\r\n"
    return output

def find_previous_version(target_version, basedir=None, flavor="", architecture=64):
    """Find version which is the closest to `version`"""
    build_dir = Path(basedir) / f"bu{flavor}"
    pattern = re.compile(rf"WinPython{flavor}-{architecture}bit-([0-9\.]+)\.(txt|md)")
    versions = [pattern.match(f).group(1) for f in os.listdir(build_dir) if pattern.match(f)]
    versions = [v for v in versions if version.parse(v) < version.parse(target_version)]
    return max(versions, key=version.parse, default=target_version)

def compare_package_indexes(version2, version1=None, basedir=None, flavor="", flavor1=None, architecture=64):
    version1 = version1 or find_previous_version(version2, basedir, flavor, architecture)
    flavor1 = flavor1 or flavor

    pi1 = PackageIndex(version1, basedir, flavor1, architecture)
    pi2 = PackageIndex(version2, basedir, flavor, architecture)

    text = (
        f"## History of changes for WinPython-{architecture}bit {version2 + flavor}\r\n\r\n"
        f"The following changes were made to WinPython-{architecture}bit distribution since version {version1 + flavor1}.\r\n\r\n"
        "<details>\r\n\r\n"
    )

    for key in PackageIndex.HEADERS:
        diff = compare_packages(pi1.packages[key], pi2.packages[key])
        if diff:
            text += f"{PackageIndex.HEADERS[key]}\r\n\r\n{diff}"

    return text + "\r\n</details>\r\n* * *\r\n"

def copy_changelogs(version, basedir, flavor="", architecture=64):
    basever = ".".join(version.split(".")[:2])
    pattern = re.compile(rf"WinPython{flavor}-{architecture}bit-{basever}[0-9\.]*\.(txt|md)")
    dest = Path(basedir) / f"bu{flavor}"
    for fname in os.listdir(CHANGELOGS_DIR):
        if pattern.match(fname):
            shutil.copyfile(CHANGELOGS_DIR / fname, dest / fname)

def write_changelog(version2, version1=None, basedir=None, flavor="", architecture=64):
    """Write changelog between version1 and version2 of WinPython"""
    copy_changelogs(version2, basedir, flavor, architecture)
    print("comparing_package_indexes", version2, basedir, flavor, architecture)
    changelog = compare_package_indexes(version2, version1, basedir, flavor, architecture=architecture)
    output_file = Path(basedir) / f"bu{flavor}" / f"WinPython{flavor}-{architecture}bit-{version2}_History.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(changelog)
    # Copy to winpython/changelogs
    shutil.copyfile(output_file, CHANGELOGS_DIR / output_file.name)

if __name__ == "__main__":
    print(compare_package_indexes("3.7.4.0", "3.7.2.0", r"C:\WinP\bd37", "Zero", architecture=32))
    write_changelog("3.7.4.0", "3.7.2.0", r"C:\WinP\bd37", "Ps2", architecture=64)
