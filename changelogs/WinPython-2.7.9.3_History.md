## History of changes for WinPython 2.7.9.3

The following changes were made to WinPython distribution since version 2.7.9.2.

### Python packages

New packages:

  * [certifi](http://pypi.python.org/pypi/certifi) 14.5.14 (Python package for providing Mozilla's CA Bundle.)
  * [cffi](http://pypi.python.org/pypi/cffi) 0.8.6 (Foreign Function Interface for Python calling C code.)
  * [funcsigs](http://pypi.python.org/pypi/funcsigs) 0.4 (Python function signatures from PEP362 for Python 2.6, 2.7 and 3.2+)
  * [jsonschema](http://pypi.python.org/pypi/jsonschema) 2.4.0 (An implementation of JSON Schema validation for Python)
  * [mistune](http://pypi.python.org/pypi/mistune) 0.5 (The fastest markdown parser in pure Python, inspired by marked.)
  * [numpy](http://numpy.scipy.org/) 1.9.2rc1+mkl (NumPy: multidimensional array processing for numbers, strings, records and objects (SciPy''s core module))
  * [numpydoc](http://pypi.python.org/pypi/numpydoc) 0.5 (Sphinx extension to support docstrings in Numpy format)
  * [pycparser](http://pypi.python.org/pypi/pycparser) 2.10 (C parser in Python)

Upgraded packages:

  * [Cython](http://www.cython.org) 0.21.2 → 0.22 (Cython is a language that makes writing C extensions for the Python language as easy as Python)
  * [Pygments](http://pygments.org) 2.0.1 → 2.0.2 (Generic syntax highlighter for general use in all kinds of software)
  * [XlsxWriter](http://pypi.python.org/pypi/XlsxWriter) 0.6.5 → 0.6.6 (A Python module for creating Excel XLSX files.)
  * [astroid](http://pypi.python.org/pypi/astroid) 1.3.2 → 1.3.4 (Rebuild a new abstract syntax tree from Python's ast (required for pylint))
  * [colorama](http://pypi.python.org/pypi/colorama) 0.3.2 → 0.3.3 (Cross-platform colored terminal text)
  * [husl](http://pypi.python.org/pypi/husl) 4.0.0 → 4.0.1 (Human-friendly HSL (Hue-Saturation-Lightness))
  * [ipython](http://ipython.org) 2.3.1 → 2.4.1 (Enhanced Python shell)
  * [ipython_sql](http://pypi.python.org/pypi/ipython_sql) 0.3.4 → 0.3.5 ()
  * [julia](http://sourceforge.net/projects/stonebig.u/files/packages) 0.1.1.6 → 0.1.1.8 (Python interface to the Julia language)
  * [llvmlite](http://pypi.python.org/pypi/llvmlite) 0.2.1 → 0.2.2 (lightweight wrapper around basic LLVM functionality)
  * [lmfit](http://pypi.python.org/pypi/lmfit) 0.8.0 → 0.8.3 (Least-Squares Minimization with Bounds and Constraints)
  * [lxml](http://pypi.python.org/pypi/lxml) 3.4.1 → 3.4.2 (Powerful and Pythonic XML processing library combining libxml2/libxslt with the ElementTree API.)
  * [mahotas](http://pypi.python.org/pypi/mahotas) 1.2.3 → 1.2.4 (Computer Vision library)
  * [matplotlib](http://matplotlib.sourceforge.net) 1.4.2 → 1.4.3 (2D plotting library (embeddable in GUIs created with PyQt))
  * [mysql_connector_python](http://pypi.python.org/pypi/mysql_connector_python) 1.2.3 → 2.0.3 (MySQL driver written in Python)
  * [numba](http://pypi.python.org/pypi/numba) 0.16.0 → 0.17.0 (compiling Python code using LLVM)
  * [oct2py](http://pypi.python.org/pypi/oct2py) 2.4.0 → 3.1.0 (Python to GNU Octave bridge --> run m-files from python.)
  * [pep8](http://pypi.python.org/pypi/pep8) 1.5.7 → 1.6.2 (Python style guide checker)
  * [pip](http://pypi.python.org/pypi/pip) 6.0.6 → 6.0.8 (A tool for installing and managing Python packages)
  * [psutil](http://code.google.com/p/psutil) 2.2.0 → 2.2.1 (Provides an interface for retrieving information on all running processes and system utilization (CPU, disk, memory, network) in a portable way)
  * [pylint](http://www.logilab.org/project/pylint) 1.4.0 → 1.4.1 (Logilab code analysis module: analyzes Python source code looking for bugs and signs of poor quality)
  * [python_dateutil](http://labix.org/python-dateutil) 2.3 → 2.4.0 (Powerful extensions to the standard datetime module)
  * [pyzmq](http://pypi.python.org/pypi/pyzmq) 14.4.1 → 14.5.0 (Lightweight and super-fast messaging based on ZeroMQ library (required for IPython Qt console))
  * [reportlab](http://www.reportlab.org) 3.1.8 → 3.1.44 (The PDF generation library)
  * [requests](http://pypi.python.org/pypi/requests) 2.5.1 → 2.5.3 (Requests is an Apache2 Licensed HTTP library, written in Python, for human beings.)
  * [rpy2](http://pypi.python.org/pypi/rpy2) 2.5.4 → 2.5.6 (Python interface to the R language (embedded R))
  * [runipy](http://pypi.python.org/pypi/runipy) 0.1.1 → 0.1.3 (Run IPython notebooks from the command line)
  * [scilab2py](http://pypi.python.org/pypi/scilab2py) 0.5 → 0.6 (Python to Scilab bridge)
  * [scipy](http://www.scipy.org) 0.15.0 → 0.15.1 (SciPy: Scientific Library for Python (advanced math, signal processing, optimization, statistics, ...))
  * [setuptools](http://pypi.python.org/pypi/setuptools) 11.3.1 → 12.3 (Download, build, install, upgrade, and uninstall Python packages - easily)
  * [spyder](https://bitbucket.org/spyder-ide/spyderlib) 2.3.2 → 2.3.3 (Scientific PYthon Development EnviRonment: designed for interactive computing and data visualisation with a simple and intuitive user interface)
  * [tornado](http://pypi.python.org/pypi/tornado) 4.0.2 → 4.1 (Scalable, non-blocking web server and tools (required for IPython notebook))

Removed packages:

  * [numpy-MKL](http://numpy.scipy.org/) 1.9.1 (NumPy: multidimensional array processing for numbers, strings, records and objects (SciPy''s core module))
  * [pyreadline](http://ipython.org/pyreadline.html) 2.0 (IPython needs this module to display color text in Windows command window)

* * *
