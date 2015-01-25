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

import os
import os.path as osp
import re
import shutil

# Local imports
from winpython import utils


CHANGELOGS_DIR = osp.join(osp.dirname(__file__), 'changelogs')
assert osp.isdir(CHANGELOGS_DIR)


class Package(object):
    # SourceForge Wiki syntax:
    PATTERN = r'\[([a-zA-Z\-\:\/\.\_0-9]*)\]\(([^\]\ ]*)\) \| ([^\|]*) \| ([^\|]*)'
    # Google Code Wiki syntax:
    PATTERN_OLD = r'\[([a-zA-Z\-\:\/\.\_0-9]*) ([^\]\ ]*)\] \| ([^\|]*) \| ([^\|]*)'

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
        try:
            self.url, self.name, self.version, self.description = \
                                    re.match(self.PATTERN_OLD, text).groups()
        except AttributeError:
            self.name, self.url, self.version, self.description = \
                                        re.match(self.PATTERN, text).groups()

    def to_wiki(self):
        return "  * [%s](%s) %s (%s)\r\n" % (self.name, self.url,
                                             self.version, self.description)

    def upgrade_wiki(self, other):
        # wheel replace '-' per '_' in key
        assert self.name.replace('-','_') == other.name.replace('-','_')
        return "  * [%s](%s) %s  %s (%s)\r\n" % (self.name, self.url,
                                other.version, self.version, self.description)


def get_basedir(version, rootdir=None):
    """Return basedir from WinPython version"""
    rootdir = rootdir if rootdir is not None else utils.ROOT_DIR
    assert rootdir is not None, "The *rootdir* directory must be specified"
    return osp.join(rootdir, 'basedir%s' % version[::2][:2])


class PackageIndex(object):
    WINPYTHON_PATTERN = r'\#\# WinPython ([0-9\.a-zA-Z]*)'
    TOOLS_LINE = '### Tools'
    PYTHON_PACKAGES_LINE = '### Python packages'
    HEADER_LINE1 = 'Name | Version | Description'
    HEADER_LINE2 = '-----|---------|------------'

    def __init__(self, version, rootdir=None, flavor=''):
        self.version = version
        self.other_packages = {}
        self.python_packages = {}
        self.flavor = flavor
        basedir = get_basedir(version, rootdir=rootdir)
        self.from_file(basedir)

    def from_file(self, basedir):
        fname = osp.join(basedir, 'build%s' % self.flavor,
                         'WinPython%s-%s.txt' % (self.flavor, self.version))
        with open(fname, 'r') as fdesc:  # python3 doesn't like 'rb'
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
                elif line in (self.HEADER_LINE1, self.HEADER_LINE2):
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
    dict1 = {} ; dict2 = {}
    for key in dict1_in:
        dict1[key.replace('-','_')] = dict1_in[key] 
    for key in dict2_in:
        dict2[key.replace('-','_')] = dict2_in[key]

    set1, set2 = set(dict1.keys()), set(dict2.keys())
    # New packages
    new = sorted(set2 - set1)
    if new:
        text += "New packages:\r\n\r\n"
        for name in new:
            package = dict2[name]
            text += package.to_wiki()
        text += '\r\n'
    # Upgraded packages
    upgraded_list = []
    for name in sorted(set1 & set2):
        package1 = dict1[name]
        package2 = dict2[name]
        if package1.version != package2.version:
            upgraded_list.append(package2.upgrade_wiki(package1))
    if upgraded_list:
        text += "Upgraded packages:\r\n\r\n%s\r\n" % "".join(upgraded_list)
    # Removed packages
    removed = sorted(set1 - set2)
    if removed:
        text += "Removed packages:\r\n\r\n"
        for name in removed:
            package = dict1[name]
            text += package.to_wiki()
        text += '\r\n'
    return text


def find_closer_version(version1, rootdir=None, flavor=''):
    """Find version which is the closest to `version`"""
    builddir = osp.join(get_basedir(version1, rootdir), 'build%s' % flavor)
    func = lambda name: re.match(r'WinPython%s-([0-9\.]*)\.txt' % flavor, name)
    versions = [func(name).groups()[0]
                for name in os.listdir(builddir) if func(name)]
    try:
        index = versions.index(version1)
    except ValueError:
        raise ValueError("Unknown version %s" % version1)
    if index == 0:
        print("No version prior to %s" % version1)
        index += 1  # we don't want to fail on this
    return versions[index-1]


def compare_package_indexes(version2, version1=None, rootdir=None, flavor=''):
    """Compare two package index Wiki pages"""
    if version1 is None:
        version1 = find_closer_version(version2, rootdir=rootdir,
                                       flavor=flavor)
    text = '\r\n'.join(["## History of changes for WinPython %s" % version2,
                        "", "The following changes were made to WinPython "
                        "distribution since version %s." % version1, "", ""])
    pi1 = PackageIndex(version1, rootdir=rootdir, flavor=flavor)
    pi2 = PackageIndex(version2, rootdir=rootdir, flavor=flavor)
    tools_text = diff_package_dicts(pi1.other_packages, pi2.other_packages)
    if tools_text:
        text += PackageIndex.TOOLS_LINE + '\r\n\r\n' + tools_text
    py_text = diff_package_dicts(pi1.python_packages, pi2.python_packages)
    if py_text:
        text += PackageIndex.PYTHON_PACKAGES_LINE + '\r\n\r\n' + py_text
    text += '* * *\r\n'
    return text


def _copy_all_changelogs(version, basedir, flavor=''):
    basever = '.'.join(version.split('.')[:2])
    for name in os.listdir(CHANGELOGS_DIR):
        if re.match(r'WinPython%s-%s([0-9\.]*)\.txt' %
                    (flavor, basever), name):
            shutil.copyfile(osp.join(CHANGELOGS_DIR, name),
                            osp.join(basedir, 'build%s' % flavor, name))


def write_changelog(version2, version1=None, rootdir=None, flavor=''):
    """Write changelog between version1 and version2 of WinPython"""
    basedir = get_basedir(version2, rootdir=rootdir)
    _copy_all_changelogs(version2, basedir, flavor=flavor)
    text = compare_package_indexes(version2, version1, rootdir=rootdir,
                                   flavor=flavor)
    fname = osp.join(basedir, 'build%s' % flavor,
                     'WinPython%s-%s_History.txt' % (flavor, version2))
    with open(fname, 'w', encoding='utf-8-sig') as fdesc:  # python 3 need
        fdesc.write(text)
    # Copy to winpython/changelogs
    shutil.copyfile(fname, osp.join(CHANGELOGS_DIR, osp.basename(fname)))


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


def test_compare(basedir, version2, version1):
    print(compare_package_indexes(basedir, version2, version1))


if __name__ == '__main__':
    # test_parse_package_index_wiki('2.7.3.3')
    # print(compare_package_indexes('2.7.3.3', '2.7.3.1'))
    # write_changelog('2.7.4.1', '2.7.4.0')
    # write_changelog('2.7.5.0', '2.7.4.1')
    write_changelog('3.3.2.1')  # , '2.7.5.0')
    write_changelog('2.7.5.1')  # , '2.7.5.0')
    # write_changelog('3.3.0.0beta2', '3.3.0.0beta1')
    # write_changelog('3.3.1.1', '3.3.1.0')
    # write_changelog('3.3.2.0', '3.3.1.1')
    # write_changelog('3.3.2.1', '3.3.2.0')
