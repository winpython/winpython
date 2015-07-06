## History of changes for WinPython 2.7.10.1

The following changes were made to WinPython distribution since version 2.7.9.5.

### Python packages

New packages:

  * [Keras](http://pypi.python.org/pypi/Keras) 0.1.1 (Theano-based Deep Learning library)
  * [bcolz](http://pypi.python.org/pypi/bcolz) 0.9.0 (columnar and compressed data containers.)
  * [cyordereddict](http://pypi.python.org/pypi/cyordereddict) 0.2.2 (Cython implementation of Python's collections.OrderedDict)
  * [cytoolz](http://pypi.python.org/pypi/cytoolz) 0.7.3 (Cython implementation of Toolz: High performance functional utilities)
  * [dask](http://pypi.python.org/pypi/dask) 0.5.0 (Minimal task scheduling abstraction)
  * [datashape](http://pypi.python.org/pypi/datashape) 0.4.5 (A data description language)
  * [dill](http://pypi.python.org/pypi/dill) 0.2.2 (serialize all of python (almost))
  * [functools32](http://pypi.python.org/pypi/functools32) 3.2.3.post1 ()
  * [multipledispatch](http://pypi.python.org/pypi/multipledispatch) 0.4.7 (A relatively sane approach to multiple dispatch in Python)
  * [odo](http://pypi.python.org/pypi/odo) 0.3.2 (Data migration in Python)
  * [toolz](http://pypi.python.org/pypi/toolz) 0.7.2 (List processing tools and functional utilities)
  * [vispy](http://pypi.python.org/pypi/vispy) 0.4.0 (Interactive visualization in Python)

Upgraded packages:

  * [Cython](http://www.cython.org) 0.22 → 0.22.1 (Cython is a language that makes writing C extensions for the Python language as easy as Python)
  * [Pillow](http://pypi.python.org/pypi/Pillow) 2.8.1 → 2.8.2 (Python Imaging Library (fork))
  * [PyQt4](http://www.riverbankcomputing.co.uk/software/pyqt/intro) 4.11.3 → 4.11.4 (Python bindings for the Qt cross platform GUI toolkit)
  * [Python](http://www.python.org/) 2.7.9 → 2.7.10 (Python programming language with standard library)
  * [SQLAlchemy](http://www.sqlalchemy.org) 1.0.4 → 1.0.5 (SQL Toolkit and Object Relational Mapper)
  * [XlsxWriter](http://pypi.python.org/pypi/XlsxWriter) 0.7.2 → 0.7.3 (A Python module for creating Excel XLSX files.)
  * [alabaster](http://pypi.python.org/pypi/alabaster) 0.7.3 → 0.7.4 (A configurable sidebar-enabled Sphinx theme)
  * [cffi](http://pypi.python.org/pypi/cffi) 0.9.2 → 1.1.2 (Foreign Function Interface for Python calling C code.)
  * [db.py](http://pypi.python.org/pypi/db.py) 0.4.1 → 0.4.4 (a db package that doesn't suck)
  * [ipython](http://ipython.org) 3.1.0 → 3.2.0 (Enhanced Python shell)
  * [ipython_sql](http://pypi.python.org/pypi/ipython_sql) 0.3.5 → 0.3.6 (RDBMS access via IPython)
  * [jedi](http://pypi.python.org/pypi/jedi) 0.8.1 → 0.9.0 (An autocompletion tool for Python that can be used for text editors)
  * [jsonschema](http://pypi.python.org/pypi/jsonschema) 2.4.0 → 2.5.1 (An implementation of JSON Schema validation for Python)
  * [llvmlite](http://pypi.python.org/pypi/llvmlite) 0.4.0 → 0.5.1 (lightweight wrapper around basic LLVM functionality)
  * [mysql_connector_python](http://pypi.python.org/pypi/mysql_connector_python) 2.0.3 → 2.0.4 (MySQL driver written in Python)
  * [nose](http://somethingaboutorange.com/mrl/projects/nose) 1.3.6 → 1.3.7 (nose is a discovery-based unittest extension (e.g. NumPy test module is using nose))
  * [numba](http://pypi.python.org/pypi/numba) 0.18.2 → 0.19.2 (compiling Python code using LLVM)
  * [oct2py](http://pypi.python.org/pypi/oct2py) 3.1.0 → 3.2.0 (Python to GNU Octave bridge --> run m-files from python.)
  * [pandas](http://pypi.python.org/pypi/pandas) 0.16.1 → 0.16.2 (Powerful data structures for data analysis, time series and statistics)
  * [pip](http://pypi.python.org/pypi/pip) 6.1.1 → 7.0.3 (A tool for installing and managing Python packages)
  * [psutil](http://code.google.com/p/psutil) 2.2.1 → 3.0.0 (Provides an interface for retrieving information on all running processes and system utilization (CPU, disk, memory, network) in a portable way)
  * [pycparser](http://pypi.python.org/pypi/pycparser) 2.12 → 2.14 (C parser in Python)
  * [pyflakes](http://pypi.python.org/pypi/pyflakes) 0.8.1 → 0.9.2 (passive checker of Python programs)
  * [pymongo](http://pypi.python.org/pypi/pymongo) 3.0.1 → 3.0.2 (Python driver for MongoDB <http://www.mongodb.org>)
  * [pytz](http://pytz.sourceforge.net/) 2015.2 → 2015.4 (World Timezone Definitions for Python)
  * [pyzmq](http://pypi.python.org/pypi/pyzmq) 14.6.0 → 14.7.0 (Lightweight and super-fast messaging based on ZeroMQ library (required for IPython Qt console))
  * [reportlab](http://www.reportlab.org) 3.1.44 → 3.2.0 (The PDF generation library)
  * [rpy2](http://pypi.python.org/pypi/rpy2) 2.5.6 → 2.6.0 (Python interface to the R language (embedded R))
  * [setuptools](http://pypi.python.org/pypi/setuptools) 15.2 → 17.1.1 (Download, build, install, upgrade, and uninstall Python packages - easily)
  * [simplejson](http://pypi.python.org/pypi/simplejson) 3.6.5 → 3.7.3 (Simple, fast, extensible JSON (JavaScript Object Notation) encoder/decoder)
  * [spyder](http://pypi.python.org/pypi/spyder) 2.3.4 → 2.3.5.2 (Scientific PYthon Development EnviRonment: designed for interactive computing and data visualisation with a simple and intuitive user interface)
  * [tornado](http://pypi.python.org/pypi/tornado) 4.1 → 4.2 (Scalable, non-blocking web server and tools (required for IPython notebook))

Removed packages:

  * [tqdm](http://pypi.python.org/pypi/tqdm) 1.0 (A Simple Python Progress Meter)

* * *
