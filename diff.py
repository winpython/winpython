# -*- coding: utf-8 -*-
#
# Copyright © 2013 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython diff script

Created on Tue Jan 29 11:56:54 2013
"""

from __future__ import print_function, with_statement

import os.path as osp
import re

# Local imports
from winpython import utils


class Package(object):
    PATTERN = r'\|\| \[([a-zA-Z\-\:\/\.\_0-9]*) ([^\]\ ]*)] \|\| ([^\|]*) \|\| ([^\|]*) \|\|'
    def __init__(self):
        self.name = None
        self.version = None
        self.description = None
        self.url = None

    def __str__(self):
        text = "%s %s" % (self.name, self.version)
        text += "\r\n%s\r\nWebsite: %s" % (self.description, self.url)
        return text
    
    def from_text(self, text):
        match = re.match(self.PATTERN, text)
        self.url, self.name, self.version, self.description = match.groups()
    
    def to_wiki(self):
        return "  * [%s %s] %s (%s)\r\n" % (self.url, self.name,
                                            self.version, self.description)
    
    def upgrade_wiki(self, other):
        assert self.name == other.name
        return "  * [%s %s] %s → %s (%s)\r\n" % (self.url, self.name,
                                other.version, self.version, self.description)


def get_basedir(version, rootdir=None):
    """Return basedir from WinPython version"""
    rootdir = rootdir if rootdir is not None else utils.ROOT_DIR
    assert rootdir is not None, "The *rootdir* directory must be specified"
    return osp.join(rootdir, 'basedir%s' % version[::2][:2])


class PackageIndex(object):
    WINPYTHON_PATTERN = r'== WinPython ([0-9\.a-zA-Z]*) =='
    TOOLS_LINE = '=== Tools ==='
    PYTHON_PACKAGES_LINE = '=== Python packages ==='
    def __init__(self, version, rootdir=None):
        self.version = version
        self.other_packages = {}
        self.python_packages = {}
        basedir = get_basedir(version, rootdir=rootdir)
        self.from_file(basedir)
    
    def from_file(self, basedir):
        fname = osp.join(basedir, 'build', 'WinPython-%s.txt' % self.version)
        with open(fname, 'rb') as fdesc:
            text = fdesc.read()
        self.from_text(text)
    
    def from_text(self, text):
        version = re.match(self.WINPYTHON_PATTERN, text).groups()[0]
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
                if tools_flag or python_flag:
                    package = Package()
                    package.from_text(line)
                    if tools_flag:
                        self.other_packages[package.name] = package
                    else:
                        self.python_packages[package.name] = package


def diff_package_dicts(dict1, dict2):
    """Return difference between package dict1 and package dict2"""
    text = ""
    set1, set2 = set(dict1.keys()), set(dict2.keys())
    # New packages
    new = set2 - set1
    if new:
        text += "New packages:\r\n\r\n"
        for name in new:
            package = dict2[name]
            text += package.to_wiki()
        text += '\r\n'
    # Upgraded packages
    upgraded_list = []
    for name in set1 & set2:
        package1 = dict1[name]
        package2 = dict2[name]
        if package1.version != package2.version:
            upgraded_list.append(package2.upgrade_wiki(package1))
    if upgraded_list:
        text += "Upgraded packages:\r\n\r\n%s\r\n" % "".join(upgraded_list)
    # Removed packages
    removed = set1 - set2
    if removed:
        text += "Removed packages:\r\n\r\n"
        for name in removed:
            package = dict1[name]
            text += package.to_wiki()
        text += '\r\n'
    return text


def compare_package_indexes(version1, version2, rootdir=None):
    """Compare two package index Wiki pages"""
    text = '\r\n'.join(["== History of changes for WinPython %s ==" % version2,
                        "", "The following changes were made to WinPython "\
                        "distribution since version %s." % version1, "", ""])
    pi1 = PackageIndex(version1, rootdir=rootdir)
    pi2 = PackageIndex(version2, rootdir=rootdir)
    tools_text = diff_package_dicts(pi1.other_packages, pi2.other_packages)
    if tools_text:
        text += PackageIndex.TOOLS_LINE + '\r\n\r\n' + tools_text
    py_text = diff_package_dicts(pi1.python_packages, pi2.python_packages)
    if py_text:
        text += PackageIndex.PYTHON_PACKAGES_LINE + '\r\n\r\n' + py_text
    text += '----\r\n'
    return text


def write_changelog(version1, version2, rootdir=None):
    """Write changelog between version1 and version2 of WinPython"""
    text = compare_package_indexes(version1, version2, rootdir=rootdir)
    basedir = get_basedir(version1, rootdir=rootdir)
    fname = osp.join(basedir, 'build', 'WinPython-%s_History.txt' % version2)
    with open(fname, 'wb') as fdesc:
        fdesc.write(text)


def test_parse_package_index_wiki(version, rootdir=None):
    """Parse the package index Wiki page"""
    pi = PackageIndex(version, rootdir=rootdir)
    utils.print_box("WinPython %s:" % pi.version)
    utils.print_box("Tools:")
    for package in pi.other_packages.values():
        print(package)
        print('')
    utils.print_box("Python packages:")
    for package in pi.python_packages.values():
        print(package)
        print('')


def test_compare(basedir, version1, version2):
    print(compare_package_indexes(basedir, version1, version2))


if __name__ == '__main__':
#    test_parse_package_index_wiki('2.7.3.3')
#    print(compare_package_indexes('2.7.3.1', '2.7.3.3'))
    write_changelog('2.7.3.0', '2.7.3.1')
    write_changelog('2.7.3.1', '2.7.3.2')
    write_changelog('2.7.3.2', '2.7.3.3')
    write_changelog('2.7.3.3', '2.7.4.0')
    write_changelog('2.7.4.0', '2.7.4.1')
    write_changelog('2.7.4.1', '2.7.4.2')
#    write_changelog('3.3.0.0beta1', '3.3.0.0beta2')
    write_changelog('3.3.0.0beta2', '3.3.1.0')
    write_changelog('3.3.1.0', '3.3.1.1')
    write_changelog('3.3.1.1', '3.3.1.2')
