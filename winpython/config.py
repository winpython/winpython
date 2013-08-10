# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

"""
WinPython utilities configuration

Created on Wed Aug 29 12:23:19 2012
"""

from spyderlib.baseconfig import add_image_path, get_module_data_path

add_image_path(get_module_data_path('winpython', relpath='images'))
add_image_path(get_module_data_path('spyderlib', relpath='images'))

def get_data_path():
    """Return package data path"""
    return get_module_data_path('winpython', relpath='data')
