## History of changes for WinPython 3.5.2.1

The following changes were made to WinPython distribution since version 3.5.1.3.

### Python packages

New packages:

  * [args](http://pypi.python.org/pypi/args) 0.1.0 (Command Arguments for Humans.)
  * [boto3](http://pypi.python.org/pypi/boto3) 1.3.1 (The AWS SDK for Python)
  * [botocore](http://pypi.python.org/pypi/botocore) 1.4.36 (Low-level, data-driven core of boto 3.)
  * [clint](http://pypi.python.org/pypi/clint) 0.5.1 (Python Command Line Interface Tools)
  * [commonmark](http://pypi.python.org/pypi/commonmark) 0.5.4 (Python parser for the CommonMark Markdown spec)
  * [distributed](http://pypi.python.org/pypi/distributed) 1.11.2 (Distributed computing)
  * [entrypoints](http://pypi.python.org/pypi/entrypoints) 0.2.2 (Discover and load entry points from installed packages)
  * [fasteners](http://pypi.python.org/pypi/fasteners) 0.14.1 (A python package that provides useful locks.)
  * [ipyleaflet](http://pypi.python.org/pypi/ipyleaflet) 0.2.1 (A Jupyter widget for dynamic Leaflet maps)
  * [isort](http://pypi.python.org/pypi/isort) 4.2.5 (A Python utility / library to sort Python imports.)
  * [jmespath](http://pypi.python.org/pypi/jmespath) 0.9.0 (JSON Matching Expressions)
  * [mccabe](http://pypi.python.org/pypi/mccabe) 0.4.0 (McCabe checker, plugin for flake8)
  * [monotonic](http://pypi.python.org/pypi/monotonic) 1.1 (An implementation of time.monotonic() for Python 2 & < 3.3)
  * [msgpack-python](http://pypi.python.org/pypi/msgpack-python) 0.4.7 (MessagePack (de)serializer.)
  * [nbsphinx](http://pypi.python.org/pypi/nbsphinx) 0.2.8 (Jupyter Notebook Tools for Sphinx)
  * [pycodestyle](http://pypi.python.org/pypi/pycodestyle) 2.0.0 (Python style guide checker)
  * [recommonmark](http://pypi.python.org/pypi/recommonmark) 0.4.0 (A markdown parser for docutils)
  * [s3fs](http://pypi.python.org/pypi/s3fs) 0.0.6 (Convenient Filesystem interface over S3)
  * [tblib](http://pypi.python.org/pypi/tblib) 1.3.0 (Traceback serialization library.)
  * [widgetsnbextension](http://pypi.python.org/pypi/widgetsnbextension) 1.2.6 (IPython HTML widgets for Jupyter)
  * [win-unicode-console](http://pypi.python.org/pypi/win-unicode-console) 0.5 (Enable Unicode input and display when running Python from Windows console.)
  * [zarr](http://pypi.python.org/pypi/zarr) 1.0.0 (A minimal implementation of chunked, compressed, N-dimensional arrays for Python.)

Upgraded packages:

  * [alabaster](http://pypi.python.org/pypi/alabaster) 0.7.7 → 0.7.8 (A configurable sidebar-enabled Sphinx theme)
  * [astroid](http://pypi.python.org/pypi/astroid) 1.4.5 → 1.4.7 (Rebuild a new abstract syntax tree from Python's ast (required for pylint))
  * [babel](http://pypi.python.org/pypi/babel) 2.2.0 → 2.3.2 (Internationalization utilities)
  * [bcolz](http://pypi.python.org/pypi/bcolz) 0.12.1 → 1.1.0 (columnar and compressed data containers.)
  * [blaze](http://pypi.python.org/pypi/blaze) 0.9.1 → 0.10.1 (Blaze)
  * [blosc](http://pypi.python.org/pypi/blosc) 1.3.0 → 1.3.3 (Blosc data compressor)
  * [bottleneck](http://pypi.python.org/pypi/bottleneck) 1.0.0 → 1.1.0 (Fast NumPy array functions written in Cython)
  * [bqplot](http://pypi.python.org/pypi/bqplot) 0.5.5 → 0.7.1 (Interactive plotting for the Jupyter notebook, using d3.js and ipywidgets.)
  * [cffi](http://pypi.python.org/pypi/cffi) 1.5.2 → 1.7.0 (Foreign Function Interface for Python calling C code.)
  * [cython](http://www.cython.org) 0.24 → 0.24.1 (Cython is a language that makes writing C extensions for the Python language as easy as Python)
  * [cytoolz](http://pypi.python.org/pypi/cytoolz) 0.7.5 → 0.8.0 (Cython implementation of Toolz: High performance functional utilities)
  * [dask](http://pypi.python.org/pypi/dask) 0.8.1 → 0.10.1 (Minimal task scheduling abstraction)
  * [datashape](http://pypi.python.org/pypi/datashape) 0.5.1 → 0.5.2 (A data description language)
  * [decorator](http://pypi.python.org/pypi/decorator) 4.0.7 → 4.0.10 (Better living through Python with decorators)
  * [flask](http://pypi.python.org/pypi/flask) 0.10.1 → 0.11.1 (A microframework based on Werkzeug, Jinja2 and good intentions)
  * [greenlet](http://pypi.python.org/pypi/greenlet) 0.4.9 → 0.4.10 (Lightweight in-process concurrent programming)
  * [h5py](http://pypi.python.org/pypi/h5py) 2.5.0 → 2.6.0 (General-purpose Python interface to HDF5 files (unlike PyTables, h5py provides direct access to the full HDF5 C library))
  * [holoviews](http://pypi.python.org/pypi/holoviews) 1.4.3 → 1.6.0 (Composable, declarative data structures for building complex visualizations easily.)
  * [imagesize](http://pypi.python.org/pypi/imagesize) 0.7.0 → 0.7.1 (Getting image size from png/jpeg/jpeg2000/gif file)
  * [ipyparallel](http://pypi.python.org/pypi/ipyparallel) 5.0.1 → 5.1.1 (Interactive Parallel Computing with IPython)
  * [ipython](http://pypi.python.org/pypi/ipython) 4.1.2 → 5.0.0 (Enhanced Python shell)
  * [ipywidgets](http://pypi.python.org/pypi/ipywidgets) 4.1.1 → 5.2.2 (IPython HTML widgets for Jupyter)
  * [joblib](http://pypi.python.org/pypi/joblib) 0.9.4 → 0.10.0 (Lightweight pipelining: using Python functions as pipeline jobs.)
  * [julia](http://pypi.python.org/pypi/julia) 0.1.1.8 → 0.1.1 (Python interface to the Julia language)
  * [jupyter-client](http://pypi.python.org/pypi/jupyter-client) 4.2.2 → 4.3.0 (Jupyter metapackage. Install all the Jupyter components in one go.)
  * [jupyter-console](http://pypi.python.org/pypi/jupyter-console) 4.1.1 → 5.0.0 (Jupyter metapackage. Install all the Jupyter components in one go.)
  * [keras](http://pypi.python.org/pypi/keras) 0.3.3 → 1.0.6 (Theano-based Deep Learning library)
  * [lazy-object-proxy](http://pypi.python.org/pypi/lazy-object-proxy) 1.2.1 → 1.2.2 (A fast and thorough lazy object proxy.)
  * [llvmlite](http://pypi.python.org/pypi/llvmlite) 0.10.0 → 0.12.1 (lightweight wrapper around basic LLVM functionality)
  * [matplotlib](http://pypi.python.org/pypi/matplotlib) 1.5.1 → 1.5.2 (2D plotting library (embeddable in GUIs created with PyQt))
  * [mistune](http://pypi.python.org/pypi/mistune) 0.7.2 → 0.7.3 (The fastest markdown parser in pure Python, inspired by marked.)
  * [nbconvert](http://pypi.python.org/pypi/nbconvert) 4.1.0 → 4.2.0 (Converting Jupyter Notebooks)
  * [netcdf4](http://pypi.python.org/pypi/netcdf4) 1.2.3.1 → 1.2.4 (python/numpy interface to netCDF library (versions 3 and 4))
  * [nltk](http://pypi.python.org/pypi/nltk) 3.2 → 3.2.1 (The Natural Language Toolkit (NLTK) is a Python package for natural language processing.)
  * [notebook](http://pypi.python.org/pypi/notebook) 4.1.0 → 4.2.1 (# Jupyter Notebook)
  * [numba](http://pypi.python.org/pypi/numba) 0.25.0 → 0.27.0 (compiling Python code using LLVM)
  * [numexpr](http://pypi.python.org/pypi/numexpr) 2.5.1 → 2.6.1 (Fast evaluation of array expressions elementwise by using a vector-based virtual machine)
  * [numpy](http://numpy.scipy.org/) 1.10.4 → 1.11.1 (NumPy: multidimensional array processing for numbers, strings, records and objects (SciPy''s core module))
  * [oct2py](http://pypi.python.org/pypi/oct2py) 3.5.3 → 3.5.9 (Python to GNU Octave bridge --> run m-files from python.)
  * [odo](http://pypi.python.org/pypi/odo) 0.4.2 → 0.5.0 (Data migration in Python)
  * [pandas](http://pypi.python.org/pypi/pandas) 0.18.0 → 0.18.1 (Powerful data structures for data analysis, time series and statistics)
  * [param](http://pypi.python.org/pypi/param) 1.3.2 → 1.4.1 (Declarative Python programming using Parameters.)
  * [partd](http://pypi.python.org/pypi/partd) 0.3.2 → 0.3.4 (Appendable key-value storage)
  * [pickleshare](http://pypi.python.org/pypi/pickleshare) 0.6 → 0.7.2 (Tiny 'shelve'-like database with concurrency support)
  * [pillow](http://pypi.python.org/pypi/pillow) 3.2.0 → 3.3.0 (Python Imaging Library (fork))
  * [pip](http://pypi.python.org/pypi/pip) 8.1.1 → 8.1.2 (A tool for installing and managing Python packages)
  * [pkginfo](http://pypi.python.org/pypi/pkginfo) 1.2.1 → 1.3.2 (Query metadatdata from sdists / bdists / installed packages.)
  * [prompt-toolkit](http://pypi.python.org/pypi/prompt-toolkit) 0.60 → 1.0.3 (Library for building powerful interactive command lines in Python)
  * [psutil](http://code.google.com/p/psutil) 4.1.0 → 4.3.0 (Provides an interface for retrieving information on all running processes and system utilization (CPU, disk, memory, network) in a portable way)
  * [ptpython](http://pypi.python.org/pypi/ptpython) 0.32 → 0.35 (Python REPL build on top of prompt_toolkit)
  * [pyflakes](http://pypi.python.org/pypi/pyflakes) 1.1.0 → 1.2.3 (passive checker of Python programs)
  * [pylint](http://www.logilab.org/project/pylint) 1.5.5 → 1.6.1 (Logilab code analysis module: analyzes Python source code looking for bugs and signs of poor quality)
  * [pyparsing](http://pyparsing.wikispaces.com/) 2.1.0 → 2.1.5 (A Python Parsing Module)
  * [pyserial](http://pypi.python.org/pypi/pyserial) 3.0.1 → 3.1.1 (Library encapsulating the access for the serial port)
  * [Python](http://www.python.org/) 3.5.1 → 3.5.2 (Python programming language with standard library)
  * [python-dateutil](http://labix.org/python-dateutil) 2.5.1 → 2.5.3 (Powerful extensions to the standard datetime module)
  * [pytz](http://pypi.python.org/pypi/pytz) 2016.3 → 2016.4 (World Timezone Definitions for Python)
  * [pywin32](http://pypi.python.org/pypi/pywin32) 220 → 220.1 (Python library for Windows)
  * [pyzmq](http://pypi.python.org/pypi/pyzmq) 15.2.0 → 15.3.0 (Lightweight and super-fast messaging based on ZeroMQ library (required for IPython Qt console))
  * [qtpy](http://pypi.python.org/pypi/qtpy) 1.0 → 1.1.1 (Provides an abstraction layer on top of the various Qt bindings (PyQt5, PyQt4 and PySide) and additional custom QWidgets.)
  * [requests](http://pypi.python.org/pypi/requests) 2.9.1 → 2.10.0 (Requests is an Apache2 Licensed HTTP library, written in Python, for human beings.)
  * [requests-toolbelt](http://pypi.python.org/pypi/requests-toolbelt) 0.6.0 → 0.6.2 (Requests is an Apache2 Licensed HTTP library, written in Python, for human beings.)
  * [rpy2](http://pypi.python.org/pypi/rpy2) 2.7.8 → 2.8.1 (Python interface to the R language (embedded R))
  * [rx](http://pypi.python.org/pypi/rx) 1.2.6 → 1.5.2 (Reactive Extensions (Rx) for Python)
  * [scipy](http://www.scipy.org) 0.17.0 → 0.18.0rc2 (SciPy: Scientific Library for Python (advanced math, signal processing, optimization, statistics, ...))
  * [seaborn](http://pypi.python.org/pypi/seaborn) 0.7.0 → 0.7.1 (statistical data visualization)
  * [setuptools](http://pypi.python.org/pypi/setuptools) 20.6.7 → 24.0.2 (Download, build, install, upgrade, and uninstall Python packages - easily)
  * [sphinx](http://pypi.python.org/pypi/sphinx) 1.4 → 1.4.5 (Tool for generating documentation which uses reStructuredText as its markup language)
  * [sqlalchemy](http://www.sqlalchemy.org) 1.0.12 → 1.0.14 (SQL Toolkit and Object Relational Mapper)
  * [statsmodels](http://pypi.python.org/pypi/statsmodels) 0.6.1 → 0.8.0rc1 (Statistical computations and models for use with SciPy)
  * [tables](http://www.pytables.org) 3.2.2 → 3.2.3 (Package based on HDF5 library for managing hierarchical datasets (extremely large amounts of data))
  * [theano](http://pypi.python.org/pypi/theano) 0.8.1 → 0.8.2 (Optimizing compiler for evaluating mathematical expressions on CPUs and GPUs.)
  * [toolz](http://pypi.python.org/pypi/toolz) 0.7.4 → 0.8.0 (List processing tools and functional utilities)
  * [tornado](http://pypi.python.org/pypi/tornado) 4.3 → 4.4 (Scalable, non-blocking web server and tools (required for IPython notebook))
  * [traitlets](http://pypi.python.org/pypi/traitlets) 4.2.1 → 4.2.2 (Traitlets Python config system)
  * [twine](http://pypi.python.org/pypi/twine) 1.6.5 → 1.7.4 (Collection of utilities for interacting with PyPI)
  * [wcwidth](http://pypi.python.org/pypi/wcwidth) 0.1.6 → 0.1.7 (Measures number of Terminal column cells of wide-character codes)
  * [werkzeug](http://pypi.python.org/pypi/werkzeug) 0.11.4 → 0.11.10 (The Swiss Army knife of Python web development)
  * [winpython](http://winpython.github.io/) 1.5.20160402 → 1.6.20160625 (WinPython distribution tools, including WPPM (package manager))
  * [wrapt](http://pypi.python.org/pypi/wrapt) 1.10.7 → 1.10.8 (A Python module for decorators, wrappers and monkey patching.)
  * [xlrd](http://pypi.python.org/pypi/xlrd) 0.9.4 → 1.0.0 (Extract data from Microsoft Excel spreadsheet files)
  * [xlsxwriter](http://pypi.python.org/pypi/xlsxwriter) 0.8.4 → 0.9.3 (A Python module for creating Excel XLSX files.)

Removed packages:

  * [castra](http://pypi.python.org/pypi/castra) 0.1.7 (On-disk partitioned store)
  * [dill](http://pypi.python.org/pypi/dill) 0.2.5 (serialize all of python (almost))
  * [path.py](http://pypi.python.org/pypi/path.py) 8.1.2 (A module wrapper for os.path)
  * [pyreadline](http://pypi.python.org/pypi/pyreadline) 2.1 (IPython needs this module to display color text in Windows command window)

* * *
