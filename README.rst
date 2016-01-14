WinPython tools
===============

Copyright © 2012-2013 Pierre Raybaut
Licensed under the terms of the MIT License
(see winpython/__init__.py for details)


Overview
--------

WinPython is a portable distribution of the Python programming 
language for Windows (http://winpython.github.io).
		
This is the `winpython` Python package, not the distribution itself.
It includes two main features:

	The WinPython Package Manager (WPPM): let you install/uninstall 
    to your WinPython distribution any standard Python package built 
    with distutils (e.g. "dummypackage-2.1.win-amd64-py3.4.‌exe")
	or with wheels (e.g. "dummypackage-2.1-py2.py3-none-any.whl")
			
	The WinPython build toolchain: make.py is the script used to 
	build a WinPython distribution from (almost) scratch.

Dependencies
------------   

* Python2 >= 2.7 or Python3 >= 3.4

* PyQt4 >= 4.11 or PyQt5 >= 5.4 (PyQt4 is recommended)

* pip >= 7.1.0 and setuptools >= 17.1.1

Requirements
------------

* 7zip (directory has to be available in PATH)

* NSIS:
    * "Large strings" special build (http://nsis.sourceforge.net/Special_Builds)
    * with TextReplace plugin installed

Installation
------------
    
From the source package (see section 'Building dependencies'), you may 
install WinPython using the integrated setup.py script based on Python 
standard library `distutils` with the following command::
    python setup.py install

Note that `distutils` does *not* uninstall previous versions of Python 
packages: it simply copies files on top of an existing installation. 
When using this command, it is thus highly recommended to uninstall 
manually any previous version of WinPython by removing the associated 
directory ('winpython' in your site-packages directory).

From the Python package index, you may simply install WinPython *and* 
upgrade an existing installation using `pip`::
    http://pypi.python.org/pypi

But the easiest way to install the last stable release of WinPython is 
by using an executable installer: http://winpython.github.io/
            
More informations
-----------------

* Downloads: https://sourceforge.net/projects/winpython/files/ 

* Development, bug reports and feature requests: https://github.com/winpython/winpython

* Discussions: http://groups.google.com/group/winpython
