## History of changes for WinPython-64bit 3.10.8.0

The following changes were made to WinPython-64bit distribution since version 3.10.5.0.

<details>
### Python packages

New packages:

  * [click_default_group_wheel](https://pypi.org/project/click_default_group_wheel) 1.2.2 (Extends click.Group to invoke a command without explicit subcommand name (packaged as a wheel))
  * [confection](https://pypi.org/project/confection) 0.0.3 ()
  * [contourpy](https://pypi.org/project/contourpy) 1.0.6 (Python library for calculating contours of 2D quadrilateral grids)
  * [duckdb](https://pypi.org/project/duckdb) 0.5.1 (DuckDB embedded database)
  * [exceptiongroup](https://pypi.org/project/exceptiongroup) 1.0.0 (Backport of PEP 654 (exception groups))
  * [filterpy](https://pypi.org/project/filterpy) 1.4.5 (Kalman filtering and optimal estimation library)
  * [linear_operator](https://pypi.org/project/linear_operator) 0.1.1 (A linear operator implementation, primarily designed for finite-dimensional positive definite operators (i.e. kernel matrices).)
  * [missingno](https://pypi.org/project/missingno) 0.5.1 (Missing data visualization module for Python.)
  * [ntlm_auth](https://pypi.org/project/ntlm_auth) 1.5.0 (Creates NTLM authentication structures)
  * [pmdarima](https://pypi.org/project/pmdarima) 2.0.1 (Python's forecast::auto.arima equivalent)
  * [requests_ntlm](https://pypi.org/project/requests_ntlm) 1.1.0 (This package allows for HTTP NTLM authentication using the requests library.)
  * [sspyrs](https://pypi.org/project/sspyrs) 0.2 (Lightweight interface for SSRS reports to python)
  * [tbats](https://pypi.org/project/tbats) 1.1.0 (BATS and TBATS for time series forecasting)
  * [waitress](https://pypi.org/project/waitress) 2.1.2 (Waitress WSGI server)
  * [whatthepatch](https://pypi.org/project/whatthepatch) 1.0.2 (A patch parsing and application library.)
  * [xgboost](https://pypi.org/project/xgboost) 1.6.1 (XGBoost Python Package)
  * [xmltodict](https://pypi.org/project/xmltodict) 0.13.0 (Makes working with XML feel like you are working with JSON)

Upgraded packages:

  * [aiohttp](https://pypi.org/project/aiohttp) 3.8.1 → 3.8.3 (Async http client/server framework (asyncio))
  * [anyio](https://pypi.org/project/anyio) 3.6.1 → 3.6.2 (High level compatibility layer for multiple asynchronous event loop implementations)
  * [astroid](https://pypi.org/project/astroid) 2.11.5 → 2.12.12 (An abstract syntax tree for Python with inference support.)
  * [astropy](https://pypi.org/project/astropy) 5.0.4 → 5.1.1 (Community-developed python astronomy tools)
  * [attrs](https://pypi.org/project/attrs) 21.4.0 → 22.1.0 (Classes Without Boilerplate)
  * [black](https://pypi.org/project/black) 22.6.0 → 22.10.0 (The uncompromising code formatter.)
  * [blis](https://pypi.org/project/blis) 0.7.7 → 0.7.9 (The Blis BLAS-like linear algebra library, as a self-contained C-extension.)
  * [botorch](https://pypi.org/project/botorch) 0.4.0 → 0.6.2 (Bayesian Optimization in PyTorch)
  * [bqplot](https://pypi.org/project/bqplot) 0.12.33 → 0.12.36 (Interactive plotting for the Jupyter notebook, using d3.js and ipywidgets.)
  * [cachelib](https://pypi.org/project/cachelib) 0.6.0 → 0.9.0 (A collection of cache libraries in the same API interface.)
  * [catalogue](https://pypi.org/project/catalogue) 2.0.7 → 2.0.8 (Super lightweight function registries for your library)
  * [certifi](https://pypi.org/project/certifi) 2022.5.18.1 → 2022.9.24 (Python package for providing Mozilla's CA Bundle.)
  * [chardet](https://pypi.org/project/chardet) 4.0.0 → 5.0.0 (Universal encoding detector for Python 2 and 3)
  * [click](https://pypi.org/project/click) 8.0.4 → 8.1.3 (Composable command line interface toolkit)
  * [clr_loader](https://pypi.org/project/clr_loader) 0.1.7 → 0.2.4 (Generic pure Python loader for .NET runtimes)
  * [colorama](https://pypi.org/project/colorama) 0.4.4 → 0.4.6 (Cross-platform colored terminal text.)
  * [colorcet](https://pypi.org/project/colorcet) 3.0.0 → 3.0.1 (Collection of perceptually uniform colormaps)
  * [coverage](https://pypi.org/project/coverage) 6.4.1 → 6.5.0 (Code coverage measurement for Python)
  * [cvxpy](https://pypi.org/project/cvxpy) 1.2.0 → 1.2.1 (A domain-specific language for modeling convex optimization problems in Python.)
  * [cymem](https://pypi.org/project/cymem) 2.0.6 → 2.0.7 (Manage calls to calloc/free through Cython)
  * [cython](https://pypi.org/project/cython) 0.29.30 → 0.29.32 (The Cython compiler for writing C extensions for the Python language.)
  * [cytoolz](https://pypi.org/project/cytoolz) 0.11.2 → 0.12.0 (Cython implementation of Toolz: High performance functional utilities)
  * [dash](https://pypi.org/project/dash) 2.4.1 → 2.6.2 (A Python framework for building reactive web-apps. Developed by Plotly.)
  * [dask](https://pypi.org/project/dask) 2022.7.0 → 2022.10.1 (Parallel PyData with Task Scheduling)
  * [dask_image](https://pypi.org/project/dask_image) 2021.12.0 → 2022.9.0 (Distributed image processing)
  * [dask_ml](https://pypi.org/project/dask_ml) 2022.1.22 → 2022.5.27 (A library for distributed and parallel machine learning)
  * [datasette](https://pypi.org/project/datasette) 0.61.1 → 0.62 (A tool for exploring and publishing data)
  * [datasette_graphql](https://pypi.org/project/datasette_graphql) 2.0.2 → 2.1.1 (Datasette plugin providing an automatic GraphQL API for your SQLite databases)
  * [datashader](https://pypi.org/project/datashader) 0.14.0 → 0.14.2 (Data visualization toolchain based on aggregating into a grid)
  * [distlib](https://pypi.org/project/distlib) 0.3.4 → 0.3.6 (Distribution utilities)
  * [distributed](https://pypi.org/project/distributed) 2022.7.0 → 2022.10.1 (Distributed scheduler for Dask)
  * [django](https://pypi.org/project/django) 4.0.5 → 4.1.2 (A high-level Python web framework that encourages rapid development and clean, pragmatic design.)
  * [fastai](https://pypi.org/project/fastai) 2.7.6 → 2.7.9 (fastai makes deep learning with PyTorch faster, more accurate, and easier)
  * [fastapi](https://pypi.org/project/fastapi) 0.78.0 → 0.85.1 (FastAPI framework, high performance, easy to learn, fast to code, ready for production)
  * [fastcore](https://pypi.org/project/fastcore) 1.4.5 → 1.5.11 (Python supercharged for fastai development)
  * [fastjsonschema](https://pypi.org/project/fastjsonschema) 2.15.3 → 2.16.2 (Fastest Python implementation of JSON schema)
  * [fastparquet](https://pypi.org/project/fastparquet) 0.8.0 → 0.8.3 (Python support for Parquet file format)
  * [fastprogress](https://pypi.org/project/fastprogress) 1.0.2 → 1.0.3 (A nested progress with plotting options for fastai)
  * [filelock](https://pypi.org/project/filelock) 3.7.1 → 3.8.0 (A platform independent file lock.)
  * [flask](https://pypi.org/project/flask) 2.1.2 → 2.2.2 (A simple framework for building complex web applications.)
  * [flask_compress](https://pypi.org/project/flask_compress) 1.12 → 1.13 (Compress responses in your Flask app with gzip.)
  * [folium](https://pypi.org/project/folium) 0.12.1 → 0.13.0 (Make beautiful maps with Leaflet.js & Python)
  * [fonttools](https://pypi.org/project/fonttools) 4.34.4 → 4.37.4 (Tools to manipulate font files)
  * [fsspec](https://pypi.org/project/fsspec) 2022.5.0 → 2022.7.1 (File-system specification)
  * [geopandas](https://pypi.org/project/geopandas) 0.10.2 → 0.12.1 (Geographic pandas extensions)
  * [gitpython](https://pypi.org/project/gitpython) 3.1.26 → 3.1.29 (Python Git Library)
  * [gpytorch](https://pypi.org/project/gpytorch) 1.5.1 → 1.9.0 (An implementation of Gaussian Processes in Pytorch)
  * [graphene](https://pypi.org/project/graphene) 3.1 → 3.1.1 (GraphQL Framework for Python)
  * [graphql_core](https://pypi.org/project/graphql_core) 3.2.1 → 3.2.3 (GraphQL implementation for Python, a port of GraphQL.js, the JavaScript reference implementation for GraphQL.)
  * [guidata](https://pypi.org/project/guidata) 2.2.1 → 2.3.0 (Automatic graphical user interfaces generation for easy dataset editing and display)
  * [guiqwt](https://pypi.org/project/guiqwt) 4.3.0 → 4.3.1 (guiqwt is a set of tools for curve and image plotting (extension to PythonQwt))
  * [holoviews](https://pypi.org/project/holoviews) 1.15.0 → 1.15.1 (Stop plotting your data - annotate your data and let it visualize itself.)
  * [hvplot](https://pypi.org/project/hvplot) 0.8.0 → 0.8.1 (A high-level plotting API for the PyData ecosystem built on HoloViews.)
  * [hypercorn](https://pypi.org/project/hypercorn) 0.13.2 → 0.14.3 (A ASGI Server based on Hyper libraries and inspired by Gunicorn.)
  * [hypothesis](https://pypi.org/project/hypothesis) 6.46.9 → 6.56.2 (A library for property-based testing)
  * [imageio](https://pypi.org/project/imageio) 2.19.3 → 2.22.1 (Library for reading and writing a wide range of image, video, scientific, and volumetric data formats.)
  * [importlib_metadata](https://pypi.org/project/importlib_metadata) 4.11.4 → 5.0.0 (Read metadata from Python packages)
  * [ipycanvas](https://pypi.org/project/ipycanvas) 0.12.0 → 0.13.1 (Interactive widgets library exposing the browser's Canvas API)
  * [ipykernel](https://pypi.org/project/ipykernel) 6.15.1 → 6.16.2 (IPython Kernel for Jupyter)
  * [ipyleaflet](https://pypi.org/project/ipyleaflet) 0.17.0 → 0.17.2 (A Jupyter widget for dynamic Leaflet maps)
  * [ipympl](https://pypi.org/project/ipympl) 0.9.1 → 0.9.2 (Matplotlib Jupyter Extension)
  * [ipywidgets](https://pypi.org/project/ipywidgets) 7.7.1 → 8.0.2 (IPython HTML widgets for Jupyter)
  * [joblib](https://pypi.org/project/joblib) 1.1.0 → 1.2.0 (Lightweight pipelining: using Python functions as pipeline jobs.)
  * [jupyter_core](https://pypi.org/project/jupyter_core) 4.11.1 → 4.11.2 (Jupyter core package. A base package on which Jupyter projects rely.)
  * [jupyter_packaging](https://pypi.org/project/jupyter_packaging) 0.12.2 → 0.12.3 (Jupyter Packaging Utilities)
  * [jupyter_server](https://pypi.org/project/jupyter_server) 1.18.1 → 1.21.0 (The Jupyter Server)
  * [jupyter_server_mathjax](https://pypi.org/project/jupyter_server_mathjax) 0.2.5 → 0.2.6 (MathJax resources as a Jupyter Server Extension.)
  * [jupyterlab](https://pypi.org/project/jupyterlab) 3.4.3 → 3.5.0 (The JupyterLab notebook server extension.)
  * [jupyterlab_lsp](https://pypi.org/project/jupyterlab_lsp) 3.10.1 → 3.10.2 (Language Server Protocol integration for JupyterLab)
  * [jupyterlab_server](https://pypi.org/project/jupyterlab_server) 2.14.0 → 2.16.1 (JupyterLab Server)
  * [jupyterlab_widgets](https://pypi.org/project/jupyterlab_widgets) 1.1.0 → 3.0.3 (JupyterLab extension providing HTML widgets)
  * [llvmlite](https://pypi.org/project/llvmlite) 0.38.1 → 0.39.1 (lightweight wrapper around basic LLVM functionality)
  * [matplotlib](https://pypi.org/project/matplotlib) 3.5.2 → 3.6.0 (Python plotting package)
  * [matplotlib_inline](https://pypi.org/project/matplotlib_inline) 0.1.3 → 0.1.6 (Inline Matplotlib backend for Jupyter)
  * [maturin](https://pypi.org/project/maturin) 0.13.0 → 0.13.6 (Build and publish crates with pyo3, rust-cpython and cffi bindings as well as rust binaries as python packages)
  * [mizani](https://pypi.org/project/mizani) 0.7.4 → 0.8.1 (Scales for Python)
  * [msvc_runtime](https://pypi.org/project/msvc_runtime) 14.29.30133 → 14.32.31326 (Install the Microsoft&#8482; Visual C++&#8482; runtime DLLs to the sys.prefix and Scripts directories)
  * [mypy](https://pypi.org/project/mypy) 0.961 → 0.982 (Optional static typing for Python)
  * [nbclassic](https://pypi.org/project/nbclassic) 0.4.2 → 0.4.7 (Jupyter Notebook as a Jupyter Server Extension.)
  * [nbclient](https://pypi.org/project/nbclient) 0.6.6 → 0.7.0 (A client library for executing notebooks. Formally nbconvert's ExecutePreprocessor.)
  * [nbformat](https://pypi.org/project/nbformat) 5.4.0 → 5.7.0 (The Jupyter Notebook format)
  * [nest_asyncio](https://pypi.org/project/nest_asyncio) 1.5.5 → 1.5.6 (Patch asyncio to allow nested event loops)
  * [networkx](https://pypi.org/project/networkx) 2.8.3 → 2.8.7 (Python package for creating and manipulating graphs and networks)
  * [notebook](https://pypi.org/project/notebook) 6.4.12 → 6.5.2 (A web-based notebook environment for interactive computing)
  * [notebook_shim](https://pypi.org/project/notebook_shim) 0.1.0 → 0.2.0 (A shim layer for notebook traits and config)
  * [numba](https://pypi.org/project/numba) 0.55.2 → 0.56.3 (compiling Python code using LLVM)
  * [numpy](https://pypi.org/project/numpy) 1.22.4+mkl → 1.23.4 (NumPy is the fundamental package for array computing with Python.)
  * [osqp](https://pypi.org/project/osqp) 0.6.2.post4 → 0.6.2.post5 (OSQP: The Operator Splitting QP Solver)
  * [outcome](https://pypi.org/project/outcome) 1.1.0 → 1.2.0 (Capture the outcome of Python function calls.)
  * [pandas](https://pypi.org/project/pandas) 1.4.3 → 1.5.1 (Powerful data structures for data analysis, time series, and statistics)
  * [panel](https://pypi.org/project/panel) 0.13.1 → 0.14.1 (A high level app and dashboarding solution for Python.)
  * [papermill](https://pypi.org/project/papermill) 2.3.4 → 2.4.0 (Parametrize and run Jupyter and nteract Notebooks)
  * [patsy](https://pypi.org/project/patsy) 0.5.2 → 0.5.3 (A Python package for describing statistical models and for building design matrices.)
  * [pillow](https://pypi.org/project/pillow) 9.1.1 → 9.3.0 (Python Imaging Library (Fork))
  * [pip](https://pypi.org/project/pip) 22.1.2 → 22.3 (The PyPA recommended tool for installing Python packages.)
  * [plotly](https://pypi.org/project/plotly) 5.8.0 → 5.11.0 (An open-source, interactive graphing library for Python)
  * [plotnine](https://pypi.org/project/plotnine) 0.9.0 → 0.10.1 (A grammar of graphics for python)
  * [polars](https://pypi.org/project/polars) 0.13.51 → 0.14.22 (Blazingly fast DataFrame library)
  * [preshed](https://pypi.org/project/preshed) 3.0.6 → 3.0.8 (Cython hash table that trusts the keys are pre-hashed)
  * [prometheus_client](https://pypi.org/project/prometheus_client) 0.14.1 → 0.15.0 (Python client for the Prometheus monitoring system.)
  * [protobuf](https://pypi.org/project/protobuf) 4.0.0rc1 → 4.21.9 (Protocol Buffers)
  * [pulp](https://pypi.org/project/pulp) 2.3 → 2.6.0 (PuLP is an LP modeler written in python. PuLP can generate MPS or LP files and call GLPK, COIN CLP/CBC, CPLEX, and GUROBI to solve linear problems.)
  * [pyarrow](https://pypi.org/project/pyarrow) 8.0.0 → 9.0.0 (Python library for Apache Arrow)
  * [pybind11](https://pypi.org/project/pybind11) 2.9.2 → 2.10.0 (Seamless operability between C++11 and Python)
  * [pydantic](https://pypi.org/project/pydantic) 1.8.2 → 1.9.1 (Data validation and settings management using python 3.6 type hinting)
  * [pygad](https://pypi.org/project/pygad) 2.16.3 → 2.17.0 (PyGAD: A Python 3 Library for Building the Genetic Algorithm and Training Machine Learning Algoithms (Keras & PyTorch).)
  * [pygments](https://pypi.org/project/pygments) 2.11.2 → 2.12.0 (Pygments is a syntax highlighting package written in Python.)
  * [pylint](https://pypi.org/project/pylint) 2.14.0 → 2.15.4 (python code static checker)
  * [pyqt5_sip](https://pypi.org/project/pyqt5_sip) 12.9.1 → 12.11.0 (The sip module support for PyQt5)
  * [pyqtgraph](https://pypi.org/project/pyqtgraph) 0.12.4 → 0.13.1 (Scientific Graphics and GUI Library for Python)
  * [Python](http://www.python.org/) 3.10.5 → 3.10.8 (Python programming language with standard library)
  * [python_lsp_server](https://pypi.org/project/python_lsp_server) 1.4.1 → 1.5.0 (Python Language Server for the Language Server Protocol)
  * [pythonnet](https://pypi.org/project/pythonnet) 3.0.0rc1 → 3.0.0.post1 (.Net and Mono integration for Python)
  * [pythonqwt](https://pypi.org/project/pythonqwt) 0.10.1 → 0.10.2 (Qt plotting widgets for Python)
  * [pytz](https://pypi.org/project/pytz) 2022.1 → 2022.4 (World timezone definitions, modern and historical)
  * [pywavelets](https://pypi.org/project/pywavelets) 1.3.0 → 1.4.1 (PyWavelets, wavelet transform module)
  * [pywinpty](https://pypi.org/project/pywinpty) 2.0.6 → 2.0.9 (Python bindings for the winpty library)
  * [pyzo](https://pypi.org/project/pyzo) 4.12.3 → 4.12.4.dev0 (the Python IDE for scientific computing)
  * [qtawesome](https://pypi.org/project/qtawesome) 1.1.1 → 1.2.1 (FontAwesome icons in PyQt and PySide applications)
  * [qtconsole](https://pypi.org/project/qtconsole) 5.3.1 → 5.3.2 (Jupyter Qt console)
  * [qtpy](https://pypi.org/project/qtpy) 2.2.0.dev0 → 2.2.1 (Provides an abstraction layer on top of the various Qt bindings (PyQt5, PyQt4 and PySide) and additional custom QWidgets.)
  * [quart](https://pypi.org/project/quart) 0.17.0 → 0.18.3 (A Python ASGI web microframework with the same API as Flask)
  * [regex](https://pypi.org/project/regex) 2022.6.2 → 2022.9.13 (Alternative regular expression module, to replace re.)
  * [reportlab](https://pypi.org/project/reportlab) 3.6.10 → 3.6.12 (The Reportlab Toolkit)
  * [requests](https://pypi.org/project/requests) 2.27.1 → 2.28.1 (Python HTTP for Humans.)
  * [scikit_learn](https://pypi.org/project/scikit_learn) 1.1.1 → 1.1.3 (A set of python modules for machine learning and data mining)
  * [scipy](https://pypi.org/project/scipy) 1.8.1 → 1.9.3 (SciPy: Scientific Library for Python)
  * [seaborn](https://pypi.org/project/seaborn) 0.11.2 → 0.12.1 (seaborn: statistical data visualization)
  * [setuptools](https://pypi.org/project/setuptools) 63.1.0 → 65.5.0 (Easily download, build, install, upgrade, and uninstall Python packages)
  * [spacy](https://pypi.org/project/spacy) 3.2.4 → 3.4.1 (Industrial-strength Natural Language Processing (NLP) in Python)
  * [spacy_legacy](https://pypi.org/project/spacy_legacy) 3.0.9 → 3.0.10 (Legacy registered functions for spaCy backwards compatibility)
  * [spacy_loggers](https://pypi.org/project/spacy_loggers) 1.0.2 → 1.0.3 (Logging utilities for SpaCy)
  * [sphinx](https://pypi.org/project/sphinx) 5.0.2 → 5.3.0 (Tool for generating documentation which uses reStructuredText as its markup language)
  * [spyder](https://pypi.org/project/spyder) 5.4.0.dev0 → 5.3.3 (The Scientific Python Development Environment)
  * [spyder_kernels](https://pypi.org/project/spyder_kernels) 2.3.2 → 2.3.3 (Jupyter kernels for Spyder's console)
  * [sqlalchemy](https://pypi.org/project/sqlalchemy) 1.4.39 → 1.4.42 (Database Abstraction Library)
  * [sqlite_fts4](https://pypi.org/project/sqlite_fts4) 1.0.1 → 1.0.3 (Python functions for working with SQLite FTS4 search)
  * [sqlite_utils](https://pypi.org/project/sqlite_utils) 3.26 → 3.29 (CLI tool and Python utility functions for manipulating SQLite databases)
  * [sqlparse](https://pypi.org/project/sqlparse) 0.4.2 → 0.4.3 (Non-validating SQL parser)
  * [srsly](https://pypi.org/project/srsly) 2.4.2 → 2.4.5 (Modern high-performance serialization utilities for Python)
  * [starlette](https://pypi.org/project/starlette) 0.19.1 → 0.20.4 (The little ASGI library that shines.)
  * [sympy](https://pypi.org/project/sympy) 1.10.1 → 1.11.1 (Computer algebra system (CAS) in Python)
  * [tabulate](https://pypi.org/project/tabulate) 0.8.9 → 0.9.0 (Pretty-print tabular data)
  * [tenacity](https://pypi.org/project/tenacity) 8.0.1 → 8.1.0 (Retry code until it succeeds)
  * [terminado](https://pypi.org/project/terminado) 0.15.0 → 0.17.0 (Terminals served to xterm.js using Tornado websockets)
  * [textdistance](https://pypi.org/project/textdistance) 4.2.2 → 4.5.0 (Compute distance between the two texts.)
  * [thinc](https://pypi.org/project/thinc) 8.0.17 → 8.1.5 (Practical Machine Learning for NLP)
  * [tomlkit](https://pypi.org/project/tomlkit) 0.11.1 → 0.11.6 (Style preserving TOML library)
  * [torch](https://pypi.org/project/torch) 1.12.0 → 1.12.1 (Tensors and Dynamic neural networks in Python with strong GPU acceleration)
  * [torchaudio](https://pypi.org/project/torchaudio) 0.12.0 → 0.12.1 (An audio package for PyTorch)
  * [torchvision](https://pypi.org/project/torchvision) 0.13.0 → 0.13.1 (image and video datasets and models for torch deep learning)
  * [traitlets](https://pypi.org/project/traitlets) 5.3.0 → 5.4.0 (Traitlets Python config system)
  * [trio](https://pypi.org/project/trio) 0.21.0 → 0.22.0 (A friendly Python library for async concurrency and I/O)
  * [typing_extensions](https://pypi.org/project/typing_extensions) 4.3.0 → 4.4.0 (Backported and Experimental Type Hints for Python 3.5+)
  * [tzdata](https://pypi.org/project/tzdata) 2022.1 → 2022.5 (Provider of IANA time zone data)
  * [uvicorn](https://pypi.org/project/uvicorn) 0.18.2 → 0.19.0 (The lightning-fast ASGI server.)
  * [wasabi](https://pypi.org/project/wasabi) 0.9.1 → 0.10.1 (A lightweight console printing and formatting toolkit)
  * [websocket_client](https://pypi.org/project/websocket_client) 1.3.3 → 1.4.1 (WebSocket client for Python. hybi13 is supported.)
  * [werkzeug](https://pypi.org/project/werkzeug) 2.1.2 → 2.2.2 (The comprehensive WSGI web application library.)
  * [widgetsnbextension](https://pypi.org/project/widgetsnbextension) 3.6.1 → 4.0.3 (IPython HTML widgets for Jupyter)
  * [winpython](http://winpython.github.io/) 4.7.20220709 → 5.1.20221030 (WinPython distribution tools, including WPPM)
  * [wsproto](https://pypi.org/project/wsproto) 1.1.0 → 1.2.0 (WebSockets state-machine based protocol implementation)
  * [xarray](https://pypi.org/project/xarray) 2022.3.0 → 2022.10.0 (N-D labeled arrays and datasets in Python)
  * [zipp](https://pypi.org/project/zipp) 3.8.0 → 3.9.0 (Backport of pathlib-compatible object wrapper for zip files)
  * [zstandard](https://pypi.org/project/zstandard) 0.17.0 → 0.19.0 (Zstandard bindings for Python)

Removed packages:

  * [altgraph](https://pypi.org/project/altgraph) 0.17.2 (Python graph (network) package)
  * [amply](https://pypi.org/project/amply) 0.1.5 (Amply allows you to load and manipulate AMPL/GLPK data as Python data structures)
  * [click_default_group](https://pypi.org/project/click_default_group) 1.2.2 (Extends click.Group to invoke a command without explicit subcommand name)
  * [jupyterlab_git](https://pypi.org/project/jupyterlab_git) 0.34.2 (A server extension for JupyterLab's git extension)
  * [mkl_service](https://pypi.org/project/mkl_service) 2.4.0 (Python bindings to some MKL service functions)
  * [pefile](https://pypi.org/project/pefile) 2021.9.3 (Python PE parsing module)
  * [pipdeptree](https://pypi.org/project/pipdeptree) 2.2.1 (Command line utility to show dependency tree of packages)
  * [pyinstaller](https://pypi.org/project/pyinstaller) 5.0.1 (PyInstaller bundles a Python application and all its dependencies into a single package.)
  * [pyinstaller_hooks_contrib](https://pypi.org/project/pyinstaller_hooks_contrib) 2022.6 (Community maintained hooks for PyInstaller)
  * [python_baseconv](https://pypi.org/project/python_baseconv) 1.2.2 (Convert numbers from base 10 integers to base X strings and back again.)


</details>
* * *
