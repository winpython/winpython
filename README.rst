WinPython tools
===============

Copyright © 2012-2013 Pierre Raybaut

Copyright © 2014-2019+ The Winpython development team https://github.com/winpython/

Licensed under the terms of the MIT License
(see winpython/__init__.py for details)


Overview
--------

WinPython is a portable distribution of the Python programming 
language for Windows (https://winpython.github.io).
		
This is the `winpython` Python package, not the distribution itself.
It includes two main features:

WinPython Package Manager (WPPM)
  a graphical layer over pip, to let you install/uninstall 
  to your WinPython distribution any standard Python package built  
  as source  (e.g. "dummypackage-2.1.zip" or "dummypackage-2.1.tar.gz") 
  or as wheel (e.g. "dummypackage-2.1-py2.py3-none-any.whl")
			
WinPython build toolchain
  make.py is the script used to 
  build a WinPython distribution from (almost) scratch.

Dependencies
------------   

* Python2 >= 2.7 or Python3 >= 3.4 (Python>= 3.7 is recommended)

* PyQt5 >= 5.6 or PySide2>=5.11 (PyQt5 >=5.12 or Pyside2 >= 5.12 is recommended)


Requirements
------------

* NSIS (for icon shortcut creations, installer can be NSIS, INNO, 7-Zip, or nothing)
    
* PyQt5 or Pyside2 is required to execute WinPython Control Panel/Ipython Qt and Qt related packages.
  if not installed, these packages will not execute.

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
upgrade an existing installation using `pip`: https://pypi.org

But the easiest way to install the last stable release of WinPython is 
by using an executable installer: https://winpython.github.io/
            
More informations
-----------------

* Downloads: https://sourceforge.net/projects/winpython/files/ 

* Development, bug reports and feature requests: https://github.com/winpython/winpython

* Discussions: https://groups.google.com/group/winpython
