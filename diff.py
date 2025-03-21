# -*- coding: utf-8 -*-
#
# Copyright © 2013 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython diff script

Created on Tue Jan 29 11:56:54 2013
"""

import os
from pathlib import Path
import re
import shutil

# Local imports
from winpython import utils


CHANGELOGS_DIR = str(Path(__file__).parent / "changelogs")
assert Path(CHANGELOGS_DIR).is_dir()


class Package(object):
    # SourceForge Wiki syntax:
    PATTERN = r"\[([a-zA-Z\-\:\/\.\_0-9]*)\]\(([^\]\ ]*)\) \| ([^\|]*) \| ([^\|]*)"
    # Google Code Wiki syntax:
    PATTERN_OLD = r"\[([a-zA-Z\-\:\/\.\_0-9]*) ([^\]\ ]*)\] \| ([^\|]*) \| ([^\|]*)"

    def __init__(self):
        self.name = None
        self.version = None
        self.description = None
        self.url = None

    def __str__(self):
        text = f"{self.name} {self.version}"
        text += f"\r\n{self.description}\r\nWebsite: {self.url}"
        return text

    def from_text(self, text):
        try:
            self.url, self.name, self.version, self.description = re.match(
                self.PATTERN_OLD, text
            ).groups()
        except AttributeError:
            self.name, self.url, self.version, self.description = re.match(
                self.PATTERN, text
            ).groups()

    def to_wiki(self):
        return f"  * [{self.name}]({self.url}) {self.version} ({self.description})\r\n"

    def upgrade_wiki(self, other):
        # wheel replace '-' per '_' in package name
        assert (
            self.name.replace("-", "_").lower() == other.name.replace("-", "_").lower()
        )
        return f"  * [{self.name}]({self.url}) {other.version} → {self.version} ({self.description})\r\n"


class PackageIndex(object):
    WINPYTHON_PATTERN = r"\#\# WinPython\-*[0-9b-t]* ([0-9\.a-zA-Z]*)"
    TOOLS_LINE = "### Tools"
    PYTHON_PACKAGES_LINE = "### Python packages"
    HEADER_LINE1 = "Name | Version | Description"
    HEADER_LINE2 = "-----|---------|------------"

    def __init__(
        self,
        version,
        basedir=None,
        flavor="",
        architecture=64,
    ):
        self.version = version
        self.other_packages = {}
        self.python_packages = {}
        self.flavor = flavor
        self.basedir = basedir
        self.architecture = architecture
        self.from_file(basedir)

    def from_file(self, basedir):
        fname = str(
            Path(CHANGELOGS_DIR)
            / f"WinPython{self.flavor}-{self.architecture}bit-{self.version}.md"
        )

        try:
            with open(fname, "r", encoding = 'utf-8') as fdesc:  # python3 doesn't like 'rb'
                text = fdesc.read()
        except:
            with open(fname, "r") as fdesc:  # python3 doesn't like 'rb'
                text = fdesc.read()            
        self.from_text(text)

    def from_text(self, text):
        version = re.match(self.WINPYTHON_PATTERN + self.flavor, text).groups()[0]
        assert version == self.version
        tools_flag = False
        python_flag = False
        for line in text.splitlines():
            if line:
                if line == self.TOOLS_LINE:
                    tools_flag = True
                    continue
                elif line == self.PYTHON_PACKAGES_LINE:
                    tools_flag = False
                    python_flag = True
                    continue
                elif line in (
                    self.HEADER_LINE1,
                    self.HEADER_LINE2,
                    "<details>",
                    "</details>",
                ):
                    continue
                if tools_flag or python_flag:
                    package = Package()
                    package.from_text(line)
                    if tools_flag:
                        self.other_packages[package.name] = package
                    else:
                        self.python_packages[package.name] = package


def diff_package_dicts(dict1_in, dict2_in):
    """Return difference between package dict1 and package dict2"""
    text = ""
    # wheel replace '-' per '_' in key
    dict1 = {}
    dict2 = {}
    for key in dict1_in:
        dict1[key.replace("-", "_").lower()] = dict1_in[key]
    for key in dict2_in:
        dict2[key.replace("-", "_").lower()] = dict2_in[key]
    set1, set2 = set(dict1.keys()), set(dict2.keys())
    # New packages
    new = sorted(set2 - set1)
    if new:
        text += "New packages:\r\n\r\n"
        for name in new:
            package = dict2[name]
            text += package.to_wiki()
        text += "\r\n"
    # Upgraded packages
    upgraded_list = []
    for name in sorted(set1 & set2):
        package1 = dict1[name]
        package2 = dict2[name]
        if package1.version != package2.version:
            upgraded_list.append(package2.upgrade_wiki(package1))
    if upgraded_list:
        text += "Upgraded packages:\r\n\r\n" + f"{''.join(upgraded_list)}" + "\r\n"
    # Removed packages
    removed = sorted(set1 - set2)
    if removed:
        text += "Removed packages:\r\n\r\n"
        for name in removed:
            package = dict1[name]
            text += package.to_wiki()
        text += "\r\n"
    return text


def find_closer_version(version1, basedir=None, flavor="", architecture=64):
    """Find version which is the closest to `version`"""
    builddir = str(Path(basedir) / f"bu{flavor}")
    func = lambda name: re.match(
        r"WinPython%s-%sbit-([0-9\.]*)\.(txt|md)" % (flavor, architecture),
        name,
    )
    versions = [func(name).groups()[0] for name in os.listdir(builddir) if func(name)]
    # versions:['3.10.0.1', '3.10.10.0', '3.10.2.0'.... '3.10.8.1', '3.10.9.0']
    try:
        index = versions.index(version1)
    except ValueError:
        raise ValueError(f"Unknown version {version1}")

    from packaging import version
    version_below = '0.0.0.0'
    for v in versions:
        if version.parse(v) > version.parse(version_below) and version.parse(v)<version.parse(version1):
            version_below = v
    if version_below =='0.0.0.0': 
        return version1
    else:
        return version_below 

def compare_package_indexes(
    version2,
    version1=None,
    basedir=None,
    flavor="",
    flavor1=None,
    architecture=64,
):
    """Compare two package index Wiki pages"""
    if version1 is None:
        version1 = find_closer_version(
            version2,
            basedir=basedir,
            flavor=flavor,
            architecture=architecture,
        )
    flavor1 = flavor1 if flavor1 is not None else flavor
    text = "\r\n".join(
        [
            f"## History of changes for WinPython-{architecture}bit {version2 + flavor}",
            "",
            f"The following changes were made to WinPython-{architecture}bit"
            f" distribution since version {version1 + flavor1}.",
            "",
            "<details>",
            "",
        ]
    )
    pi1 = PackageIndex(
        version1,
        basedir=basedir,
        flavor=flavor1,
        architecture=architecture,
    )
    pi2 = PackageIndex(
        version2,
        basedir=basedir,
        flavor=flavor,
        architecture=architecture,
    )
    tools_text = diff_package_dicts(pi1.other_packages, pi2.other_packages)
    if tools_text:
        text += PackageIndex.TOOLS_LINE + "\r\n\r\n" + tools_text
    py_text = diff_package_dicts(pi1.python_packages, pi2.python_packages)
    if py_text:
        text += PackageIndex.PYTHON_PACKAGES_LINE + "\r\n\r\n" + py_text
    text += "\r\n</details>\r\n* * *\r\n"
    return text


def _copy_all_changelogs(version, basedir, flavor="", architecture=64):
    basever = ".".join(version.split(".")[:2])
    for name in os.listdir(CHANGELOGS_DIR):
        if re.match(
            r"WinPython%s-%sbit-%s([0-9\.]*)\.(txt|md)"
            % (flavor, architecture, basever),
            name,
        ):
            shutil.copyfile(
                str(Path(CHANGELOGS_DIR) / name),
                str(Path(basedir) / f"bu{flavor}" / name),
            )


def write_changelog(
    version2,
    version1=None,
    basedir=None,
    flavor="",
    architecture=64,
):
    """Write changelog between version1 and version2 of WinPython"""
    _copy_all_changelogs(
        version2,
        basedir,
        flavor=flavor,
        architecture=architecture,
    )
    print(
        "comparing_package_indexes",
        version2,
        basedir,
        flavor,
        architecture,
    )
    text = compare_package_indexes(
        version2,
        version1,
        basedir=basedir,
        flavor=flavor,
        architecture=architecture,
    )
    fname = str(
        Path(basedir)
        / f"bu{flavor}"
        / f"WinPython{flavor}-{architecture}bit-{version2}_History.md"
    )

    with open(fname, "w", encoding="utf-8-sig") as fdesc:  # python 3 need
        fdesc.write(text)
    # Copy to winpython/changelogs
    shutil.copyfile(fname, str(Path(CHANGELOGS_DIR) / Path(fname).name))


def test_parse_package_index_wiki(version, basedir=None, flavor="", architecture=64):
    """Parse the package index Wiki page"""
    pi = PackageIndex(
        version,
        basedir=basedir,
        flavor=flavor,
        architecture=architecture,
    )
    utils.print_box(f"WinPython {pi.version}:")
    utils.print_box("Tools:")
    for package in pi.other_packages.values():
        print(package)
        print("")
    utils.print_box("Python packages:")
    for package in pi.python_packages.values():
        print(package)
        print("")


def test_compare(basedir, version2, version1, architecture=64):
    print(
        compare_package_indexes(
            basedir,
            version2,
            version1,
            architecture=architecture,
        )
    )


if __name__ == "__main__":
    print(
        compare_package_indexes(
            version2="3.7.4.0",
            version1="3.7.2.0",
            basedir=r"C:\WinP\bd37",
            flavor="Zero",
            flavor1="Zero",
            architecture=32,
        )
    )
    write_changelog(
        version2="3.7.4.0",
        version1="3.7.2.0",
        basedir=r"C:\WinP\bd37",
        flavor="Ps2",
        architecture=64,
    )
    # test_parse_package_index_wiki('2.7.3.3')
    # print(compare_package_indexes('2.7.3.3', '2.7.3.1'))
    # write_changelog('2.7.4.1', '2.7.4.0')
    # write_changelog('3.3.0.0beta2', '3.3.0.0beta1')
