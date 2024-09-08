WinPython tools
===============

Copyright @ 2012-2013 Pierre Raybaut

Copyright @ 2014-2024+ The Winpython development team https://github.com/winpython/

Licensed under the terms of the MIT License
(see winpython/__init__.py for details)


Overview
--------

WinPython is a portable distribution of the Python programming 
language for Windows (https://winpython.github.io).
		
This is the `winpython` Python package, not the distribution itself.
It includes two main features:

WinPython Package Manager (WPPM)
  a complementary tool to navigate provided package list or register WinPython. 
  pip is the recommanded way to add or remove packages
			
WinPython build toolchain
  make.py is the script used to 
  build a WinPython distribution from (almost) scratch.

Dependencies
------------   

* Python3 >= 3.8


Requirements
------------

* installer can be 7-Zip or nothing (just .zip-it)


Installation
------------
    
From the source package (see section 'Building dependencies'), you may 
install WinPython using the following commands:

**python -m pip install flit**

**python -m flit build**

**python -m pip install --no-index --trusted-host=None  --find-links=.\dist winpython**

But the easiest way to install the last stable release of WinPython is 
by using an executable installer: https://winpython.github.io/
            
More informations
-----------------

* Downloads: https://sourceforge.net/projects/winpython/files/ 

* Development, bug reports and feature requests: https://github.com/winpython/winpython

* Discussions: https://groups.google.com/group/winpython
