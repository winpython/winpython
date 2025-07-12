WinPython tools
===============

Copyright 2012-2013 Pierre Raybaut

Copyright 2014-2025+ The Winpython development team: https://github.com/winpython/

Licensed under the terms of the MIT License
(see wppm/__init__.py for details)


Overview
--------

WinPython is a portable distribution of the Python programming 
language for Windows: https://winpython.github.io
		
This is the `wppm` Python package and build toolchain repository, not the distribution itself.
It includes two main features:

WinPython Package Manager (WPPM)
  a complementary tool to navigate provided packages, install packages from included Wheelhouse, or register WinPython. 
  pip is the recommanded way to add or remove packages otherwise
			
WinPython build toolchain
  generate_a_winpython_distro.bat and make.py are the toolchain used to 
  build a WinPython distribution from (almost) scratch.

WinPython set of Wheel
  You can get also the equivalent of the WinPython distribution by using one of the provided pylock.toml
  or by using provided requirements-with-hash.txt until pip does support pylock.toml files
  

Dependencies
------------   

* Python3 >= 3.10


Requirements
------------

* installer can be 7-Zip or nothing (just .zip-it)


Wppm build 
----------
    
From the source package (see section 'Building dependencies'), you may 
build WPPM using the following commands:

.. code-block:: bash

   python -m pip install flit
   python -m flit build

Winpython Distribution wheels installation
------------------------------------------
    
To only install the wheels assembled per WinPython Distribution, you may

.. code-block:: bash

   python -m pip install --no-deps --require-hashes https://github.com/winpython/winpython/releases/download/16.6.20250620final/requir.64-3_13_5_0slim.txt

A pylock file is also available, when you package manager can handle it

.. code-block:: text

   https://github.com/winpython/winpython/releases/download/16.6.20250620final/pylock.64-3_13_5_0slim.toml

But the easiest way to install the last stable release of WinPython is 
by using a zipped distribution with or without auto-extractor: https://winpython.github.io/
            
More information
----------------

* Downloads: https://sourceforge.net/projects/winpython/files/ or https://github.com/winpython/winpython/releases

* Development, bug reports, discussions and feature requests: https://github.com/winpython/winpython

* Discussions: https://github.com/winpython/winpython/discussions
