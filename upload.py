# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 11:43:54 2013

@author: pierre
"""

from __future__ import print_function

import sys
import os.path as osp
import re

# Local imports
import googlecode_upload as gu
import make
from winpython.py3compat import configparser as cp


def get_hg_user_password():
    """Get Hg user and password infos from configuration file (hgrc)"""
    fname = osp.join(osp.dirname(__name__), ".hg", "hgrc")
    hgrc = cp.ConfigParser()
    hgrc.read(fname)
    defpath = hgrc.get("paths", "default")
    match = re.match(r'https://([a-zA-Z0-9\.\_\%]*):([\S]*)'\
                     r'@winpython.googlecode.com/hg/', defpath)
    user = match.group(1).replace('%40', '@')
    password = match.group(2)
    return user, password


def upload_installer(version, architecture):
    """Upload to WinPython GoogleCode project"""
    assert architecture in (32, 64)
    file_path = osp.join(make.get_basedir(version), "build",
                         "WinPython-%dbit-%s.exe" % (architecture, version))
    summary = "WinPython %dbit %s" % (architecture, version)
    
    user, password = get_hg_user_password()
    labels = ["Featured", "Type-Installer", "OpSys-Windows"]
    
    status, reason, url = gu.upload_find_auth(file_path, "winpython",
                                              summary, labels, user, password)
    if url:
        print('Uploaded: %s' % url)
    else:
        print('An error occurred. Your file was not uploaded.',
              file=sys.stderr)
        print('Google Code upload server said: %s (%s)' % (reason, status),
              file=sys.stderr)

if __name__ == '__main__':
    import time
    for version in ("3.3.2.3", "2.7.5.3"):
        for architecture in (64, 32):
            print(time.ctime())
            upload_installer(version, architecture)
            print()
