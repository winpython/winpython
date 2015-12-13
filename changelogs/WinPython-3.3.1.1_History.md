== History of changes for WinPython 3.3.1.1 ==

The following changes were made to WinPython distribution since version 3.3.1.0.

=== Internals ===

The following changes were made to WinPython tools (`winpython` Python package), including WPPM, WPCP and the distribution generation script (`make.py` and its dependencies):
  * WinPython Control Panel: added shortcut to command prompt
  * Bugfix: all launchers now accept command line options -- Example, for executing IPython Qt console without pylab mode enabled, just create a shortcut pointing to "IPython Qt console.exe" and add the option "--pylab=None"
  * Added launcher for IPython notebook
  * WinPython registration: now registers entries in HKCU\Software\Python\PythonCore. In other words, any distutils Python package will see WinPython distribution as a standard installed Python distribution

=== Python packages ===

Upgraded packages:

  * [http://formlayout.googlecode.com formlayout] 1.0.12 → 1.0.13 (Module for creating form dialogs/widgets to edit various type of parameters without having to write any GUI code)
  * [http://pypi.python.org/pypi/distribute distribute] 0.6.36 → 0.6.38 (Download, build, install, upgrade, and uninstall Python packages - easily)
  * [http://pypi.python.org/pypi/simplejson simplejson] 3.1.3 → 3.2.0 (Simple, fast, extensible JSON (JavaScript Object Notation) encoder/decoder)
  * [http://pypi.python.org/pypi/mahotas mahotas] 0.9.8 → 0.99 (Computer Vision library)
  * [http://code.google.com/p/psutil psutil] 0.7.0 → 0.7.1 (Provides an interface for retrieving information on all running processes and system utilization (CPU, disk, memory, network) in a portable way)
  * [http://code.google.com/p/winpython winpython] 0.12 → 0.13 (WinPython distribution tools, including WPPM (package manager))

----
