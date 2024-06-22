## History of changes for WinPython-64bit 3.12.4.1

The following changes were made to WinPython-64bit distribution since version 3.12.3.0.

<details>
### Python packages

New packages:

  * [adbc_driver_manager](https://pypi.org/project/adbc_driver_manager) 0.11.0 (A generic entrypoint for ADBC drivers.)
  * [ansicolors](https://pypi.org/project/ansicolors) 1.1.8 (ANSI colors for Python)
  * [astropy_iers_data](https://pypi.org/project/astropy_iers_data) 0.2024.4.29.0.28.48 (IERS Earth Rotation and Leap Second tables for the astropy core package)
  * [cartopy](https://pypi.org/project/cartopy) 0.23.0 (A Python library for cartographic visualizations with Matplotlib)
  * [dask_expr](https://pypi.org/project/dask_expr) 1.1.2 (High Level Expressions for Dask )
  * [email_validator](https://pypi.org/project/email_validator) 2.1.1 (A robust email address syntax and deliverability validation library.)
  * [fastapi_cli](https://pypi.org/project/fastapi_cli) 0.0.4 (Run and manage FastAPI apps from the command line with FastAPI CLI. 🚀)
  * [httptools](https://pypi.org/project/httptools) 0.6.1 (A collection of framework independent HTTP protocol utils.)
  * [jaraco_context](https://pypi.org/project/jaraco_context) 5.3.0 (Useful decorators and context managers)
  * [jaraco_functools](https://pypi.org/project/jaraco_functools) 4.0.1 (Functools like those found in stdlib)
  * [jupyter_leaflet](https://pypi.org/project/jupyter_leaflet) 0.19.1 (ipyleaflet extensions for JupyterLab and Jupyter Notebook)
  * [kornia_rs](https://pypi.org/project/kornia_rs) 0.1.3 (Low level implementations for computer vision in Rust)
  * [pyshp](https://pypi.org/project/pyshp) 2.3.1 (Pure Python read/write support for ESRI Shapefile format)
  * [typer](https://pypi.org/project/typer) 0.12.3 (Typer, build great CLIs. Easy to code. Based on Python type hints.)
  * [watchfiles](https://pypi.org/project/watchfiles) 0.21.0 (Simple, modern and high performance file watching and code reload in python.)

Upgraded packages:

  * [accelerate](https://pypi.org/project/accelerate) 0.23.0 → 0.28.0 (Accelerate)
  * [aiohttp](https://pypi.org/project/aiohttp) 3.9.3 → 3.9.5 (Async http client/server framework (asyncio))
  * [alabaster](https://pypi.org/project/alabaster) 0.7.13 → 0.7.16 (A light, configurable Sphinx theme)
  * [alembic](https://pypi.org/project/alembic) 1.12.1 → 1.13.1 (A database migration tool for SQLAlchemy.)
  * [altair](https://pypi.org/project/altair) 5.2.0 → 5.3.0 (Vega-Altair: A declarative statistical visualization library for Python.)
  * [anyio](https://pypi.org/project/anyio) 4.3.0 → 4.4.0 (High level compatibility layer for multiple asynchronous event loop implementations)
  * [anywidget](https://pypi.org/project/anywidget) 0.7.1 → 0.9.12 (custom jupyter widgets made easy)
  * [array_api_compat](https://pypi.org/project/array_api_compat) 1.4.1 → 1.7.1 (A wrapper around NumPy and other array libraries to make them compatible with the Array API standard)
  * [asgiref](https://pypi.org/project/asgiref) 3.7.2 → 3.8.1 (ASGI specs, helper code, and adapters)
  * [astropy](https://pypi.org/project/astropy) 5.3.4 → 6.1.0 (Astronomy and astrophysics core library)
  * [azure_core](https://pypi.org/project/azure_core) 1.29.5 → 1.30.1 (Microsoft Azure Core Library for Python)
  * [azure_cosmos](https://pypi.org/project/azure_cosmos) 4.5.1 → 4.6.0 (Microsoft Azure Cosmos Client Library for Python)
  * [azure_identity](https://pypi.org/project/azure_identity) 1.15.0 → 1.16.0 (Microsoft Azure Identity Library for Python)
  * [babel](https://pypi.org/project/babel) 2.13.1 → 2.15.0 (Internationalization utilities)
  * [black](https://pypi.org/project/black) 24.2.0 → 24.4.2 (The uncompromising code formatter.)
  * [bleach](https://pypi.org/project/bleach) 6.0.0 → 6.1.0 (An easy safelist-based HTML-sanitizing tool.)
  * [bokeh](https://pypi.org/project/bokeh) 3.4.0 → 3.4.1 (Interactive plots and applications in the browser from Python)
  * [branca](https://pypi.org/project/branca) 0.6.0 → 0.7.2 (Generate complex HTML+JS pages with Python)
  * [build](https://pypi.org/project/build) 1.1.1 → 1.2.1 (A simple, correct Python build frontend)
  * [cachelib](https://pypi.org/project/cachelib) 0.10.2 → 0.13.0 (A collection of cache libraries in the same API interface.)
  * [cachetools](https://pypi.org/project/cachetools) 5.3.1 → 5.3.3 (Extensible memoizing collections and decorators)
  * [certifi](https://pypi.org/project/certifi) 2023.11.17 → 2024.6.2 (Python package for providing Mozilla's CA Bundle.)
  * [charset_normalizer](https://pypi.org/project/charset_normalizer) 3.2.0 → 3.3.2 (The Real First Universal Charset Detector. Open, modern and actively maintained alternative to Chardet.)
  * [clarabel](https://pypi.org/project/clarabel) 0.7.1 → 0.9.0 (Clarabel Conic Interior Point Solver for Rust / Python)
  * [colorcet](https://pypi.org/project/colorcet) 3.0.1 → 3.1.0 (Collection of perceptually uniform colormaps)
  * [comm](https://pypi.org/project/comm) 0.1.4 → 0.2.2 (Jupyter Python Comm implementation, for usage in ipykernel, xeus-python etc.)
  * [contourpy](https://pypi.org/project/contourpy) 1.2.0 → 1.2.1 (Python library for calculating contours of 2D quadrilateral grids)
  * [cookiecutter](https://pypi.org/project/cookiecutter) 2.3.0 → 2.6.0 (A command-line utility that creates projects from project templates, e.g. creating a Python package project from a Python package project template.)
  * [coverage](https://pypi.org/project/coverage) 7.3.2 → 7.5.3 (Code coverage measurement for Python)
  * [dash](https://pypi.org/project/dash) 2.14.1 → 2.17.0 (A Python framework for building reactive web-apps. Developed by Plotly.)
  * [dask](https://pypi.org/project/dask) 2023.10.1 → 2024.5.2 (Parallel PyData with Task Scheduling)
  * [dask_image](https://pypi.org/project/dask_image) 2023.8.1 → 2024.5.3 (Distributed image processing)
  * [datasette](https://pypi.org/project/datasette) 0.64.5 → 0.64.6 (An open source multi-tool for exploring and publishing data)
  * [datashader](https://pypi.org/project/datashader) 0.16.0 → 0.16.2 (Data visualization toolchain based on aggregating into a grid)
  * [distlib](https://pypi.org/project/distlib) 0.3.6 → 0.3.8 (Distribution utilities)
  * [distributed](https://pypi.org/project/distributed) 2023.10.1 → 2024.5.2 (Distributed scheduler for Dask)
  * [django](https://pypi.org/project/django) 4.2.5 → 5.0.6 (A high-level Python web framework that encourages rapid development and clean, pragmatic design.)
  * [dnspython](https://pypi.org/project/dnspython) 2.4.2 → 2.6.1 (DNS toolkit)
  * [duckdb](https://pypi.org/project/duckdb) 0.10.1 → 1.0.0 (DuckDB in-process database)
  * [fast_histogram](https://pypi.org/project/fast_histogram) 0.12 → 0.14 (Fast simple 1D and 2D histograms)
  * [fastapi](https://pypi.org/project/fastapi) 0.109.1 → 0.111.0 (FastAPI framework, high performance, easy to learn, fast to code, ready for production)
  * [filelock](https://pypi.org/project/filelock) 3.12.4 → 3.14.0 (A platform independent file lock.)
  * [flask](https://pypi.org/project/flask) 3.0.2 → 3.0.3 (A simple framework for building complex web applications.)
  * [folium](https://pypi.org/project/folium) 0.14.0 → 0.16.0 (Make beautiful maps with Leaflet.js & Python)
  * [fonttools](https://pypi.org/project/fonttools) 4.44.0 → 4.51.0 (Tools to manipulate font files)
  * [fsspec](https://pypi.org/project/fsspec) 2023.9.2 → 2024.3.1 (File-system specification)
  * [geopandas](https://pypi.org/project/geopandas) 0.14.0 → 0.14.4 (Geographic pandas extensions)
  * [geopy](https://pypi.org/project/geopy) 2.4.0 → 2.4.1 (Python Geocoding Toolbox)
  * [guidata](https://pypi.org/project/guidata) 3.4.1 → 3.5.0 (Automatic GUI generation for easy dataset editing and display)
  * [hatchling](https://pypi.org/project/hatchling) 1.21.1 → 1.24.2 (Modern, extensible Python build backend)
  * [holoviews](https://pypi.org/project/holoviews) 1.18.3 → 1.19.0 (A high-level plotting API for the PyData ecosystem built on HoloViews.)
  * [huggingface_hub](https://pypi.org/project/huggingface_hub) 0.21.4 → 0.23.0 (Client library to download and publish models, datasets and other repos on the huggingface.co hub)
  * [hvplot](https://pypi.org/project/hvplot) 0.9.2 → 0.10.0 (A high-level plotting API for the PyData ecosystem built on HoloViews.)
  * [hypercorn](https://pypi.org/project/hypercorn) 0.14.4 → 0.16.0 (A ASGI Server based on Hyper libraries and inspired by Gunicorn)
  * [hypothesis](https://pypi.org/project/hypothesis) 6.87.1 → 6.100.5 (A library for property-based testing)
  * [idna](https://pypi.org/project/idna) 3.4 → 3.7 (Internationalized Domain Names in Applications (IDNA))
  * [imageio](https://pypi.org/project/imageio) 2.31.1 → 2.33.1 (Library for reading and writing a wide range of image, video, scientific, and volumetric data formats.)
  * [imbalanced_learn](https://pypi.org/project/imbalanced_learn) 0.12.2 → 0.12.3 (Toolbox for imbalanced dataset in machine learning.)
  * [importlib_metadata](https://pypi.org/project/importlib_metadata) 6.8.0 → 7.1.0 (Read metadata from Python packages)
  * [ipycanvas](https://pypi.org/project/ipycanvas) 0.13.1 → 0.13.2 (Interactive widgets library exposing the browser's Canvas API)
  * [ipyleaflet](https://pypi.org/project/ipyleaflet) 0.18.2 → 0.19.1 (A Jupyter widget for dynamic Leaflet maps)
  * [ipympl](https://pypi.org/project/ipympl) 0.9.3 → 0.9.4 (Matplotlib Jupyter Extension)
  * [ipython](https://pypi.org/project/ipython) 8.22.2 → 8.25.0 (IPython: Productive Interactive Computing)
  * [isort](https://pypi.org/project/isort) 5.12.0 → 5.13.2 (A Python utility / library to sort Python imports.)
  * [itsdangerous](https://pypi.org/project/itsdangerous) 2.1.2 → 2.2.0 (Safely pass data to untrusted environments and back.)
  * [jaraco_classes](https://pypi.org/project/jaraco_classes) 3.3.0 → 3.4.0 (Utility functions for Python class constructs)
  * [joblib](https://pypi.org/project/joblib) 1.3.2 → 1.4.2 (Lightweight pipelining with Python functions)
  * [jsonschema_specifications](https://pypi.org/project/jsonschema_specifications) 2023.7.1 → 2023.12.1 (The JSON Schema meta-schemas and vocabularies, exposed as a Registry)
  * [jupyter_bokeh](https://pypi.org/project/jupyter_bokeh) 3.0.7 → 4.0.5 (A Jupyter extension for rendering Bokeh content.)
  * [jupyter_client](https://pypi.org/project/jupyter_client) 8.6.0 → 8.6.2 (Jupyter protocol implementation and client libraries)
  * [jupyter_core](https://pypi.org/project/jupyter_core) 5.5.0 → 5.7.2 (Jupyter core package. A base package on which Jupyter projects rely.)
  * [jupyter_events](https://pypi.org/project/jupyter_events) 0.9.0 → 0.10.0 (Jupyter Event System library)
  * [jupyter_lsp](https://pypi.org/project/jupyter_lsp) 2.2.0 → 2.2.5 (Multi-Language Server WebSocket proxy for Jupyter Notebook/Lab server)
  * [jupyter_server](https://pypi.org/project/jupyter_server) 2.12.5 → 2.14.1 (The backend—i.e. core services, APIs, and REST endpoints—to Jupyter web applications.)
  * [jupyter_server_terminals](https://pypi.org/project/jupyter_server_terminals) 0.4.4 → 0.5.3 (A Jupyter Server Extension Providing Terminals.)
  * [jupyterlab](https://pypi.org/project/jupyterlab) 4.1.5 → 4.2.2 (JupyterLab computational environment)
  * [jupyterlab_pygments](https://pypi.org/project/jupyterlab_pygments) 0.2.2 → 0.3.0 (Pygments theme using JupyterLab CSS variables)
  * [jupyterlab_server](https://pypi.org/project/jupyterlab_server) 2.25.4 → 2.27.2 (A set of server components for JupyterLab and JupyterLab like applications.)
  * [jupyterlab_widgets](https://pypi.org/project/jupyterlab_widgets) 3.0.10 → 3.0.11 (Jupyter interactive widgets for JupyterLab)
  * [keras](https://pypi.org/project/keras) 3.1.1 → 3.3.3 (Multi-backend Keras.)
  * [keyring](https://pypi.org/project/keyring) 24.2.0 → 25.2.1 (Store and access your passwords safely.)
  * [kornia](https://pypi.org/project/kornia) 0.7.1 → 0.7.2 (Open Source Differentiable Computer Vision Library for PyTorch)
  * [langchain](https://pypi.org/project/langchain) 0.1.13 → 0.2.5 (Building applications with LLMs through composability)
  * [langchain_core](https://pypi.org/project/langchain_core) 0.1.35 → 0.2.7 (Building applications with LLMs through composability)
  * [langchain_text_splitters](https://pypi.org/project/langchain_text_splitters) 0.0.1 → 0.2.1 (LangChain text splitting utilities)
  * [langsmith](https://pypi.org/project/langsmith) 0.1.33 → 0.1.77 (Client library to connect to the LangSmith LLM Tracing and Evaluation Platform.)
  * [lazy_loader](https://pypi.org/project/lazy_loader) 0.3 → 0.4 (Makes it easy to load subpackages and functions on demand.)
  * [llvmlite](https://pypi.org/project/llvmlite) 0.42.0 → 0.43.0 (lightweight wrapper around basic LLVM functionality)
  * [lmfit](https://pypi.org/project/lmfit) 1.0.3 → 1.3.1 (Least-Squares Minimization with Bounds and Constraints)
  * [lxml](https://pypi.org/project/lxml) 5.1.0 → 5.2.2 (Powerful and Pythonic XML processing library combining libxml2/libxslt with the ElementTree API.)
  * [matplotlib](https://pypi.org/project/matplotlib) 3.8.3 → 3.9.0 (Python plotting package)
  * [matplotlib_inline](https://pypi.org/project/matplotlib_inline) 0.1.6 → 0.1.7 (Inline Matplotlib backend for Jupyter)
  * [mizani](https://pypi.org/project/mizani) 0.9.2 → 0.11.4 (Scales for Python)
  * [ml_dtypes](https://pypi.org/project/ml_dtypes) 0.3.2 → 0.4.0 (stand-alone implementation of several NumPy dtype extensions used in machine learning libraries)
  * [more_itertools](https://pypi.org/project/more_itertools) 9.0.0 → 10.2.0 (More routines for operating on iterables, beyond itertools)
  * [msvc_runtime](https://pypi.org/project/msvc_runtime) 14.38.33135 → 14.40.33807 (Install the Microsoft™ Visual C++™ runtime DLLs to the sys.prefix and Scripts directories)
  * [mutagen](https://pypi.org/project/mutagen) 1.46.0 → 1.47.0 (read and write audio tags for many formats)
  * [mypy](https://pypi.org/project/mypy) 1.9.0 → 1.10.0 (Optional static typing for Python)
  * [namex](https://pypi.org/project/namex) 0.0.7 → 0.0.8 (A simple utility to separate the implementation of your Python package and its public API surface.)
  * [nbformat](https://pypi.org/project/nbformat) 5.10.3 → 5.10.4 (The Jupyter Notebook format)
  * [nest_asyncio](https://pypi.org/project/nest_asyncio) 1.5.6 → 1.6.0 (Patch asyncio to allow nested event loops)
  * [networkx](https://pypi.org/project/networkx) 3.2.1 → 3.3 (Python package for creating and manipulating graphs and networks)
  * [notebook](https://pypi.org/project/notebook) 7.1.2 → 7.2.1 (Jupyter Notebook - A web-based notebook environment for interactive computing)
  * [notebook_shim](https://pypi.org/project/notebook_shim) 0.2.3 → 0.2.4 (A shim layer for notebook traits and config)
  * [numba](https://pypi.org/project/numba) 0.59.1 → 0.60.0 (compiling Python code using LLVM)
  * [numexpr](https://pypi.org/project/numexpr) 2.8.7 → 2.10.0 (Fast numerical expression evaluator for NumPy)
  * [numpydoc](https://pypi.org/project/numpydoc) 1.3 → 1.6.0 (Sphinx extension to support docstrings in Numpy format)
  * [openai](https://pypi.org/project/openai) 1.14.3 → 1.33.0 (The official Python library for the openai API)
  * [opencv_python](https://pypi.org/project/opencv_python) 4.9.0.80 → 4.10.0.82 (Wrapper package for OpenCV python bindings.)
  * [packaging](https://pypi.org/project/packaging) 23.2 → 24.1 (Core utilities for Python packages)
  * [pandas](https://pypi.org/project/pandas) 2.2.1 → 2.2.2 (Powerful data structures for data analysis, time series, and statistics)
  * [panel](https://pypi.org/project/panel) 1.4.1 → 1.4.4 (The powerful data exploration & web app framework for Python.)
  * [papermill](https://pypi.org/project/papermill) 2.5.1a1 → 2.6.0 (Parameterize and run Jupyter and nteract Notebooks)
  * [parso](https://pypi.org/project/parso) 0.8.3 → 0.8.4 (A Python Parser)
  * [pillow](https://pypi.org/project/pillow) 10.2.0 → 10.3.0 (Python Imaging Library (Fork))
  * [pint](https://pypi.org/project/pint) 0.19.2 → 0.23 (Physical quantities module)
  * [platformdirs](https://pypi.org/project/platformdirs) 3.8.1 → 4.2.2 (A small Python package for determining appropriate platform-specific dirs, e.g. a `user data dir`.)
  * [plotly](https://pypi.org/project/plotly) 5.20.0 → 5.22.0 (An open-source, interactive data visualization library for Python)
  * [plotnine](https://pypi.org/project/plotnine) 0.12.4 → 0.13.6 (A Grammar of Graphics for Python)
  * [pluggy](https://pypi.org/project/pluggy) 1.0.0 → 1.5.0 (plugin and hook calling mechanisms for python)
  * [polars](https://pypi.org/project/polars) 0.20.17 → 0.20.31 (Blazingly fast DataFrame library)
  * [psutil](https://pypi.org/project/psutil) 5.9.5 → 5.9.8 (Cross-platform lib for process and system monitoring in Python.)
  * [psygnal](https://pypi.org/project/psygnal) 0.9.5 → 0.11.1 (Fast python callback/event system modeled after Qt Signals)
  * [pyarrow](https://pypi.org/project/pyarrow) 14.0.1 → 16.1.0 (Python library for Apache Arrow)
  * [pycparser](https://pypi.org/project/pycparser) 2.21 → 2.22 (C parser in Python)
  * [pycryptodomex](https://pypi.org/project/pycryptodomex) 3.18.0 → 3.20.0 (Cryptographic library for Python)
  * [pyct](https://pypi.org/project/pyct) 0.4.8 → 0.5.0 (Python package common tasks for users (e.g. copy examples, fetch data, ...))
  * [pydantic](https://pypi.org/project/pydantic) 2.6.4 → 2.7.1 (Data validation using Python type hints)
  * [pydantic_core](https://pypi.org/project/pydantic_core) 2.16.3 → 2.18.2 (Core functionality for Pydantic validation and serialization)
  * [pydeck](https://pypi.org/project/pydeck) 0.8.0 → 0.9.1 (Widget for deck.gl maps)
  * [pyerfa](https://pypi.org/project/pyerfa) 2.0.1.1 → 2.0.1.4 (Python bindings for ERFA)
  * [pygments](https://pypi.org/project/pygments) 2.16.1 → 2.18.0 (Pygments is a syntax highlighting package written in Python.)
  * [pyjwt](https://pypi.org/project/pyjwt) 2.4.0 → 2.8.0 (JSON Web Token implementation in Python)
  * [pymongo](https://pypi.org/project/pymongo) 4.5.0 → 4.7.2 (Python driver for MongoDB <http://www.mongodb.org>)
  * [pynndescent](https://pypi.org/project/pynndescent) 0.5.11 → 0.5.12 (Nearest Neighbor Descent)
  * [pyodbc](https://pypi.org/project/pyodbc) 5.0.1 → 5.1.0 (DB API module for ODBC)
  * [pyomo](https://pypi.org/project/pyomo) 6.7.0 → 6.7.2 (Pyomo: Python Optimization Modeling Objects)
  * [pyparsing](https://pypi.org/project/pyparsing) 3.0.9 → 3.1.2 (pyparsing module - Classes and methods to define and execute parsing grammars)
  * [pyproject_hooks](https://pypi.org/project/pyproject_hooks) 1.0.0 → 1.1.0 (Wrappers to call pyproject.toml-based build backend hooks.)
  * [pyqtgraph](https://pypi.org/project/pyqtgraph) 0.13.4 → 0.13.7 (Scientific Graphics and GUI Library for Python)
  * [pyro_ppl](https://pypi.org/project/pyro_ppl) 1.8.4 → 1.9.0 (A Python library for probabilistic modeling and inference)
  * [pytest](https://pypi.org/project/pytest) 7.4.2 → 8.2.0 (pytest: simple powerful testing with Python)
  * [Python](http://www.python.org/) 3.12.3 → 3.12.4 (Python programming language with standard library)
  * [python_dotenv](https://pypi.org/project/python_dotenv) 1.0.0 → 1.0.1 (Read key-value pairs from a .env file and set them as environment variables)
  * [python_multipart](https://pypi.org/project/python_multipart) 0.0.5 → 0.0.9 (A streaming multipart parser for Python)
  * [pytoolconfig](https://pypi.org/project/pytoolconfig) 1.2.4 → 1.3.1 (Python tool configuration)
  * [pyzmq](https://pypi.org/project/pyzmq) 25.1.2 → 26.0.3 (Python bindings for 0MQ)
  * [qdarkstyle](https://pypi.org/project/qdarkstyle) 3.2 → 3.2.3 (The most complete dark/light style sheet for C++/Python and Qt applications)
  * [qtconsole](https://pypi.org/project/qtconsole) 5.5.1 → 5.5.2 (Jupyter Qt console)
  * [rasterio](https://pypi.org/project/rasterio) 1.3.9 → 1.3.10 (Fast and direct raster I/O for use with Numpy and SciPy)
  * [referencing](https://pypi.org/project/referencing) 0.30.2 → 0.31.1 (JSON Referencing + Python)
  * [reportlab](https://pypi.org/project/reportlab) 4.0.4 → 4.2.0 (The Reportlab Toolkit)
  * [requests_toolbelt](https://pypi.org/project/requests_toolbelt) 0.10.1 → 1.0.0 (A utility belt for advanced users of python-requests)
  * [scikit_image](https://pypi.org/project/scikit_image) 0.22.0 → 0.23.2 (Image processing in Python)
  * [scikit_learn](https://pypi.org/project/scikit_learn) 1.4.1.post1 → 1.5.0 (A set of python modules for machine learning and data mining)
  * [scipy](https://pypi.org/project/scipy) 1.12.0 → 1.13.1 (Fundamental algorithms for scientific computing in Python)
  * [setuptools](https://pypi.org/project/setuptools) 69.2.0 → 69.5.1 (Easily download, build, install, upgrade, and uninstall Python packages)
  * [shapely](https://pypi.org/project/shapely) 2.0.1 → 2.0.4 (Manipulation and analysis of geometric objects)
  * [simplejson](https://pypi.org/project/simplejson) 3.17.6 → 3.19.2 (Simple, fast, extensible JSON encoder/decoder for Python)
  * [soupsieve](https://pypi.org/project/soupsieve) 2.3.2.post1 → 2.5 (A modern CSS selector implementation for Beautiful Soup.)
  * [spyder](https://pypi.org/project/spyder) 5.5.4 → 5.5.5 (The Scientific Python Development Environment)
  * [spyder_kernels](https://pypi.org/project/spyder_kernels) 2.5.1 → 2.5.2 (Jupyter kernels for Spyder's console)
  * [sqlite_bro](https://pypi.org/project/sqlite_bro) 0.12.2 → 0.13.1 (a graphic SQLite Client in 1 Python file)
  * [stack_data](https://pypi.org/project/stack_data) 0.6.1 → 0.6.3 (Extract data from python stack frames and tracebacks for informative displays)
  * [starlette](https://pypi.org/project/starlette) 0.35.1 → 0.37.2 (The little ASGI library that shines.)
  * [statsmodels](https://pypi.org/project/statsmodels) 0.14.1 → 0.14.2 (Statistical computations and models for Python)
  * [streamlit](https://pypi.org/project/streamlit) 1.32.2 → 1.35.0 (A faster way to build and share data apps)
  * [sympy](https://pypi.org/project/sympy) 1.12 → 1.12.1 (Computer algebra system (CAS) in Python)
  * [terminado](https://pypi.org/project/terminado) 0.17.0 → 0.18.1 (Tornado websocket backend for the Xterm.js Javascript terminal emulator library.)
  * [threadpoolctl](https://pypi.org/project/threadpoolctl) 3.1.0 → 3.5.0 (threadpoolctl)
  * [tqdm](https://pypi.org/project/tqdm) 4.65.0 → 4.66.4 (Fast, Extensible Progress Meter)
  * [trio](https://pypi.org/project/trio) 0.25.0 → 0.25.1 (A friendly Python library for async concurrency and I/O)
  * [uvicorn](https://pypi.org/project/uvicorn) 0.26.0 → 0.29.0 (The lightning-fast ASGI server.)
  * [virtualenv](https://pypi.org/project/virtualenv) 20.23.0 → 20.26.2 (Virtual Python Environment builder)
  * [wcwidth](https://pypi.org/project/wcwidth) 0.2.9 → 0.2.13 (Measures the displayed width of unicode strings in a terminal)
  * [websocket_client](https://pypi.org/project/websocket_client) 1.6.4 → 1.8.0 (WebSocket client for Python with low level API options)
  * [werkzeug](https://pypi.org/project/werkzeug) 3.0.1 → 3.0.3 (The comprehensive WSGI web application library.)
  * [winpython](http://winpython.github.io/) 7.5.20240410 → 8.2.20240618 (WinPython distribution tools, including WPPM)
  * [xarray](https://pypi.org/project/xarray) 2024.2.0 → 2024.6.0 (N-D labeled arrays and datasets in Python)

Removed packages:

  * [ansi2html](https://pypi.org/project/ansi2html) 1.9.1 (Convert text with ANSI color codes to HTML or to LaTeX)
  * [asciitree](https://pypi.org/project/asciitree) 0.3.3 (Draws ASCII trees.)
  * [brewer2mpl](https://pypi.org/project/brewer2mpl) 1.4.1 (Connect colorbrewer2.org color maps to Python and matplotlib)
  * [dataclasses_json](https://pypi.org/project/dataclasses_json) 0.5.7 (Easily serialize dataclasses to and from JSON)
  * [deprecation](https://pypi.org/project/deprecation) 2.1.0 (A library to handle automated deprecations)
  * [editables](https://pypi.org/project/editables) 0.3 (Editable installations)
  * [emcee](https://pypi.org/project/emcee) 3.1.4 (The Python ensemble sampling toolkit for MCMC)
  * [fasteners](https://pypi.org/project/fasteners) 0.18 (A python package that provides useful locks)
  * [feather_format](https://pypi.org/project/feather_format) 0.4.1 (Simple wrapper library to the Apache Arrow-based Feather File Format)
  * [hatch](https://pypi.org/project/hatch) 1.9.3 (Modern, extensible Python project management)
  * [highspy](https://pypi.org/project/highspy) 1.7.1.dev1 (A thin set of pybind11 wrappers to HiGHS)
  * [hyperlink](https://pypi.org/project/hyperlink) 21.0.0 (A featureful, immutable, and correct URL for Python.)
  * [jupyter_packaging](https://pypi.org/project/jupyter_packaging) 0.12.3 (Jupyter Packaging Utilities.)
  * [jupyter_server_mathjax](https://pypi.org/project/jupyter_server_mathjax) 0.2.6 (MathJax resources as a Jupyter Server Extension.)
  * [jupyter_sphinx](https://pypi.org/project/jupyter_sphinx) 0.4.0 (Jupyter Sphinx Extensions)
  * [langchain_community](https://pypi.org/project/langchain_community) 0.0.29 (Community contributed LangChain integrations.)
  * [loky](https://pypi.org/project/loky) 3.4.0 (A robust implementation of concurrent.futures.ProcessPoolExecutor)
  * [lz4](https://pypi.org/project/lz4) 4.3.3 (LZ4 Bindings for Python)
  * [marshmallow](https://pypi.org/project/marshmallow) 3.12.1 (A lightweight library for converting complex datatypes to and from native Python datatypes.)
  * [marshmallow_enum](https://pypi.org/project/marshmallow_enum) 1.5.1 (Enum field for Marshmallow)
  * [nbdime](https://pypi.org/project/nbdime) 4.0.1 (Diff and merge of Jupyter Notebooks)
  * [nbval](https://pypi.org/project/nbval) 0.9.6 (A py.test plugin to validate Jupyter notebooks)
  * [numcodecs](https://pypi.org/project/numcodecs) 0.12.1 (A Python package providing buffer compression and transformation codecs for use in data storage and communication applications.)
  * [pyaml](https://pypi.org/project/pyaml) 20.4.0 (PyYAML-based module to produce pretty and readable YAML-serialized data)
  * [pygad](https://pypi.org/project/pygad) 3.2.0 (PyGAD: A Python Library for Building the Genetic Algorithm and Training Machine Learning Algoithms (Keras & PyTorch).)
  * [pyopengl](https://pypi.org/project/pyopengl) 3.1.7 (Standard OpenGL bindings for Python)
  * [pystache](https://pypi.org/project/pystache) 0.5.4 (Mustache for Python)
  * [scikit_optimize](https://pypi.org/project/scikit_optimize) 0.10.1 (Sequential model-based optimization toolbox.)
  * [snakeviz](https://pypi.org/project/snakeviz) 2.1.0 (A web-based viewer for Python profiler output)
  * [supersmoother](https://pypi.org/project/supersmoother) 0.4 (Python implementation of Friedman's Supersmoother)
  * [typing_inspect](https://pypi.org/project/typing_inspect) 0.8.0 (Runtime inspection utilities for typing module.)
  * [userpath](https://pypi.org/project/userpath) 1.8.0 (Cross-platform tool for adding locations to the user PATH)
  * [zarr](https://pypi.org/project/zarr) 2.16.1 (An implementation of chunked, compressed, N-dimensional arrays for Python)


</details>
* * *
