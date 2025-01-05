## History of changes for WinPython-64bit 3.12.8.0slim

The following changes were made to WinPython-64bit distribution since version 3.12.6.0slim.

<details>
### Python packages

New packages:

  * [aiohappyeyeballs](https://pypi.org/project/aiohappyeyeballs) 2.4.4 (Happy Eyeballs for asyncio)
  * [anthropic](https://pypi.org/project/anthropic) 0.42.0 (The official Python library for the anthropic API)
  * [eval_type_backport](https://pypi.org/project/eval_type_backport) 0.2.2 (Like `typing._eval_type`, but lets older Python versions use newer typing features.)
  * [google_auth](https://pypi.org/project/google_auth) 2.37.0 (Google Authentication Library)
  * [griffe](https://pypi.org/project/griffe) 1.5.4 (Signatures for entire Python programs)
  * [groq](https://pypi.org/project/groq) 0.13.1 (The official Python library for the groq API)
  * [jsonpatch](https://pypi.org/project/jsonpatch) 1.33 (Apply JSON-Patches (RFC 6902) )
  * [jsonpath_python](https://pypi.org/project/jsonpath_python) 1.0.6 (A more powerful JSONPath implementation in modern python)
  * [langchain](https://pypi.org/project/langchain) 0.3.13 (Building applications with LLMs through composability)
  * [langchain_core](https://pypi.org/project/langchain_core) 0.3.28 (Building applications with LLMs through composability)
  * [langchain_text_splitters](https://pypi.org/project/langchain_text_splitters) 0.3.4 (LangChain text splitting utilities)
  * [langsmith](https://pypi.org/project/langsmith) 0.2.6 (Client library to connect to the LangSmith LLM Tracing and Evaluation Platform.)
  * [logfire_api](https://pypi.org/project/logfire_api) 2.11.0 (Shim for the Logfire SDK which does nothing unless Logfire is installed)
  * [mistralai](https://pypi.org/project/mistralai) 1.2.5 (Python Client SDK for the Mistral AI API.)
  * [osqp](https://pypi.org/project/osqp) 0.6.7.post1 (OSQP: The Operator Splitting QP Solver)
  * [propcache](https://pypi.org/project/propcache) 0.2.1 (Accelerated property cache)
  * [pyasn1](https://pypi.org/project/pyasn1) 0.4.8 (ASN.1 types and codecs)
  * [pyasn1_modules](https://pypi.org/project/pyasn1_modules) 0.2.8 (A collection of ASN.1-based protocols modules.)
  * [pydantic_ai](https://pypi.org/project/pydantic_ai) 0.0.15 (Agent Framework / shim to use Pydantic with LLMs)
  * [pydantic_ai_slim](https://pypi.org/project/pydantic_ai_slim) 0.0.15 (Agent Framework / shim to use Pydantic with LLMs, slim package)
  * [qdldl](https://pypi.org/project/qdldl) 0.1.7.post4 (QDLDL, a free LDL factorization routine.)
  * [rsa](https://pypi.org/project/rsa) 4.7.2 (Pure-Python RSA implementation)
  * [termcolor](https://pypi.org/project/termcolor) 2.5.0 (ANSI color formatting for output in terminal)
  * [tiktoken](https://pypi.org/project/tiktoken) 0.8.0 (tiktoken is a fast BPE tokeniser for use with OpenAI's models)
  * [typing_inspect](https://pypi.org/project/typing_inspect) 0.9.0 (Runtime inspection utilities for typing module.)

Upgraded packages:

  * [adbc_driver_manager](https://pypi.org/project/adbc_driver_manager) 0.11.0 → 1.3.0 (A generic entrypoint for ADBC drivers.)
  * [aiohttp](https://pypi.org/project/aiohttp) 3.9.5 → 3.11.11 (Async http client/server framework (asyncio))
  * [altair](https://pypi.org/project/altair) 5.4.1 → 5.5.0 (Vega-Altair: A declarative statistical visualization library for Python.)
  * [anyio](https://pypi.org/project/anyio) 4.4.0 → 4.7.0 (High level compatibility layer for multiple asynchronous event loop implementations)
  * [astropy](https://pypi.org/project/astropy) 6.1.0 → 6.1.6 (Astronomy and astrophysics core library)
  * [astropy_iers_data](https://pypi.org/project/astropy_iers_data) 0.2024.4.29.0.28.48 → 0.2024.12.23.0.33.24 (IERS Earth Rotation and Leap Second tables for the astropy core package)
  * [babel](https://pypi.org/project/babel) 2.15.0 → 2.16.0 (Internationalization utilities)
  * [black](https://pypi.org/project/black) 24.8.0 → 24.10.0 (The uncompromising code formatter.)
  * [bokeh](https://pypi.org/project/bokeh) 3.5.1 → 3.6.1 (Interactive plots and applications in the browser from Python)
  * [branca](https://pypi.org/project/branca) 0.7.2 → 0.8.0 (Generate complex HTML+JS pages with Python)
  * [build](https://pypi.org/project/build) 1.2.1 → 1.2.2.post1 (A simple, correct Python build frontend)
  * [cachetools](https://pypi.org/project/cachetools) 5.3.3 → 5.4.0 (Extensible memoizing collections and decorators)
  * [cffi](https://pypi.org/project/cffi) 1.16.0 → 1.17.1 (Foreign Function Interface for Python calling C code.)
  * [charset_normalizer](https://pypi.org/project/charset_normalizer) 3.3.2 → 3.4.0 (The Real First Universal Charset Detector. Open, modern and actively maintained alternative to Chardet.)
  * [contourpy](https://pypi.org/project/contourpy) 1.2.1 → 1.3.1 (Python library for calculating contours of 2D quadrilateral grids)
  * [cvxpy](https://pypi.org/project/cvxpy) 1.5.0 → 1.6.0 (A domain-specific language for modeling convex optimization problems in Python.)
  * [dask](https://pypi.org/project/dask) 2024.7.1 → 2024.12.1 (Parallel PyData with Task Scheduling)
  * [dask_expr](https://pypi.org/project/dask_expr) 1.1.9 → 1.1.21 (High Level Expressions for Dask )
  * [distributed](https://pypi.org/project/distributed) 2024.7.1 → 2024.12.1 (Distributed scheduler for Dask)
  * [duckdb](https://pypi.org/project/duckdb) 1.0.0 → 1.1.3 (DuckDB in-process database)
  * [fastapi](https://pypi.org/project/fastapi) 0.111.1 → 0.115.6 (FastAPI framework, high performance, easy to learn, fast to code, ready for production)
  * [fiona](https://pypi.org/project/fiona) 1.9.5 → 1.10.1 (Fiona reads and writes spatial data files)
  * [folium](https://pypi.org/project/folium) 0.17.0 → 0.18.0 (Make beautiful maps with Leaflet.js & Python)
  * [fonttools](https://pypi.org/project/fonttools) 4.51.0 → 4.55.3 (Tools to manipulate font files)
  * [frozenlist](https://pypi.org/project/frozenlist) 1.4.1 → 1.5.0 (A list-like structure which implements collections.abc.MutableSequence)
  * [greenlet](https://pypi.org/project/greenlet) 3.0.3 → 3.1.1 (Lightweight in-process concurrent programming)
  * [guidata](https://pypi.org/project/guidata) 3.6.2 → 3.7.1 (Automatic GUI generation for easy dataset editing and display)
  * [h5py](https://pypi.org/project/h5py) 3.10.0 → 3.12.1 (Read and write HDF5 files from Python)
  * [hatchling](https://pypi.org/project/hatchling) 1.25.0 → 1.27.0 (Modern, extensible Python build backend)
  * [holoviews](https://pypi.org/project/holoviews) 1.19.1 → 1.20.0 (A high-level plotting API for the PyData ecosystem built on HoloViews.)
  * [httpie](https://pypi.org/project/httpie) 3.2.3 → 3.2.4 (HTTPie: modern, user-friendly command-line HTTP client for the API era.)
  * [httpx](https://pypi.org/project/httpx) 0.27.0 → 0.27.2 (The next generation HTTP client.)
  * [huggingface_hub](https://pypi.org/project/huggingface_hub) 0.24.5 → 0.27.0 (Client library to download and publish models, datasets and other repos on the huggingface.co hub)
  * [hvplot](https://pypi.org/project/hvplot) 0.10.0 → 0.11.2 (A high-level plotting API for the PyData ecosystem built on HoloViews.)
  * [jellyfish](https://pypi.org/project/jellyfish) 1.0.3 → 1.1.3 (Approximate and phonetic matching of strings.)
  * [jiter](https://pypi.org/project/jiter) 0.5.0 → 0.8.2 (Fast iterable JSON parser.)
  * [jupyter](https://pypi.org/project/jupyter) 1.0.0 → 1.1.1 (Jupyter metapackage. Install all the Jupyter components in one go.)
  * [jupyterlab](https://pypi.org/project/jupyterlab) 4.2.5 → 4.3.4 (JupyterLab computational environment)
  * [keras](https://pypi.org/project/keras) 3.5.0 → 3.7.0 (Multi-backend Keras)
  * [kiwisolver](https://pypi.org/project/kiwisolver) 1.4.5 → 1.4.7 (A fast implementation of the Cassowary constraint solver)
  * [llvmlite](https://pypi.org/project/llvmlite) 0.43.0 → 0.44.0rc2 (lightweight wrapper around basic LLVM functionality)
  * [lxml](https://pypi.org/project/lxml) 5.2.2 → 5.3.0 (Powerful and Pythonic XML processing library combining libxml2/libxslt with the ElementTree API.)
  * [matplotlib](https://pypi.org/project/matplotlib) 3.9.2 → 3.10.0 (Python plotting package)
  * [ml_dtypes](https://pypi.org/project/ml_dtypes) 0.4.0 → 0.5.0 ()
  * [multidict](https://pypi.org/project/multidict) 6.0.5 → 6.1.0 (multidict implementation)
  * [mypy](https://pypi.org/project/mypy) 1.11.1 → 1.14.0 (Optional static typing for Python)
  * [narwhals](https://pypi.org/project/narwhals) 1.5.5 → 1.15.2 (Extremely lightweight compatibility layer between dataframe libraries)
  * [networkx](https://pypi.org/project/networkx) 3.3 → 3.4.2 (Python package for creating and manipulating graphs and networks)
  * [nltk](https://pypi.org/project/nltk) 3.8.1 → 3.9.1 (Natural Language Toolkit)
  * [notebook](https://pypi.org/project/notebook) 7.2.1 → 7.3.1 (Jupyter Notebook - A web-based notebook environment for interactive computing)
  * [numba](https://pypi.org/project/numba) 0.60.0 → 0.61.0rc2 (compiling Python code using LLVM)
  * [numpy](https://pypi.org/project/numpy) 2.0.1 → 2.1.3 (Fundamental package for array computing in Python)
  * [openai](https://pypi.org/project/openai) 1.42.0 → 1.58.1 (The official Python library for the openai API)
  * [optree](https://pypi.org/project/optree) 0.11.0 → 0.13.1 (Optimized PyTree Utilities.)
  * [orjson](https://pypi.org/project/orjson) 3.9.15 → 3.10.12 (Fast, correct Python JSON library supporting dataclasses, datetimes, and numpy)
  * [packaging](https://pypi.org/project/packaging) 24.1 → 24.2 (Core utilities for Python packages)
  * [pandas](https://pypi.org/project/pandas) 2.2.2 → 2.2.3 (Powerful data structures for data analysis, time series, and statistics)
  * [panel](https://pypi.org/project/panel) 1.5.0b4 → 1.5.4 (The powerful data exploration & web app framework for Python.)
  * [pillow](https://pypi.org/project/pillow) 10.4.0 → 11.0.0 (Python Imaging Library (Fork))
  * [pip](https://pypi.org/project/pip) 24.2 → 24.3.1 (The PyPA recommended tool for installing Python packages.)
  * [pkginfo](https://pypi.org/project/pkginfo) 1.9.6 → 1.11.2 (Query metadata from sdists / bdists / installed packages.)
  * [plotly](https://pypi.org/project/plotly) 5.23.0 → 5.24.1 (An open-source, interactive data visualization library for Python)
  * [plotpy](https://pypi.org/project/plotpy) 2.6.2 → 2.7.0 (Curve and image plotting tools for Python/Qt applications)
  * [polars](https://pypi.org/project/polars) 1.6.0 → 1.18.0 (Blazingly fast DataFrame library)
  * [prompt_toolkit](https://pypi.org/project/prompt_toolkit) 3.0.47 → 3.0.48 (Library for building powerful interactive command lines in Python)
  * [pyarrow](https://pypi.org/project/pyarrow) 17.0.0 → 18.1.0 (Python library for Apache Arrow)
  * [pybind11](https://pypi.org/project/pybind11) 2.13.1 → 2.13.6 (Seamless operability between C++11 and Python)
  * [pydantic](https://pypi.org/project/pydantic) 2.8.2 → 2.10.4 (Data validation using Python type hints)
  * [pydantic_core](https://pypi.org/project/pydantic_core) 2.20.1 → 2.27.2 (Core functionality for Pydantic validation and serialization)
  * [pymongo](https://pypi.org/project/pymongo) 4.7.2 → 4.10.1 (Python driver for MongoDB <http://www.mongodb.org>)
  * [pyodbc](https://pypi.org/project/pyodbc) 5.1.0 → 5.2.0 (DB API module for ODBC)
  * [Python](http://www.python.org/) 3.12.6 → 3.12.8 (Python programming language with standard library)
  * [pythonqwt](https://pypi.org/project/pythonqwt) 0.12.7 → 0.14.2 (Qt plotting widgets for Python)
  * [pywin32](https://pypi.org/project/pywin32) 306 → 308 (Python for Window Extensions)
  * [pywinpty](https://pypi.org/project/pywinpty) 2.0.12 → 2.0.14 (Pseudo terminal support for Windows from Python.)
  * [pyyaml](https://pypi.org/project/pyyaml) 6.0.1 → 6.0.2 (YAML parser and emitter for Python)
  * [pyzmq](https://pypi.org/project/pyzmq) 26.0.3 → 26.2.0 (Python bindings for 0MQ)
  * [rapidfuzz](https://pypi.org/project/rapidfuzz) 3.9.3 → 3.9.6 (rapid fuzzy string matching)
  * [regex](https://pypi.org/project/regex) 2023.10.3 → 2024.11.6 (Alternative regular expression module, to replace re.)
  * [requests](https://pypi.org/project/requests) 2.31.0 → 2.32.3 (Python HTTP for Humans.)
  * [rich](https://pypi.org/project/rich) 13.7.1 → 13.9.4 (Render rich text, tables, progress bars, syntax highlighting, markdown and more to the terminal)
  * [rpds_py](https://pypi.org/project/rpds_py) 0.13.2 → 0.22.3 (Python bindings to Rust's persistent data structures (rpds))
  * [scikit_image](https://pypi.org/project/scikit_image) 0.24.0 → 0.25.0 (Image processing in Python)
  * [scikit_learn](https://pypi.org/project/scikit_learn) 1.5.1 → 1.6.0 (A set of python modules for machine learning and data mining)
  * [scs](https://pypi.org/project/scs) 3.2.4.post1 → 3.2.7 (Splitting conic solver)
  * [setuptools](https://pypi.org/project/setuptools) 72.2.0 → 75.6.0 (Easily download, build, install, upgrade, and uninstall Python packages)
  * [simplejson](https://pypi.org/project/simplejson) 3.19.2 → 3.19.3 (Simple, fast, extensible JSON encoder/decoder for Python)
  * [sqlalchemy](https://pypi.org/project/sqlalchemy) 2.0.30 → 2.0.35 (Database Abstraction Library)
  * [starlette](https://pypi.org/project/starlette) 0.37.2 → 0.41.3 (The little ASGI library that shines.)
  * [statsmodels](https://pypi.org/project/statsmodels) 0.14.2 → 0.14.4 (Statistical computations and models for Python)
  * [streamlit](https://pypi.org/project/streamlit) 1.37.1 → 1.41.1 (A faster way to build and share data apps)
  * [trio](https://pypi.org/project/trio) 0.26.2 → 0.27.0 (A friendly Python library for async concurrency and I/O)
  * [trove_classifiers](https://pypi.org/project/trove_classifiers) 2023.2.20 → 2024.10.21.16 (Canonical source for classifiers on PyPI (pypi.org).)
  * [ujson](https://pypi.org/project/ujson) 5.8.0 → 5.10.0 (Ultra fast JSON encoder and decoder for Python)
  * [websockets](https://pypi.org/project/websockets) 12.0 → 13.1 (An implementation of the WebSocket Protocol (RFC 6455 & 7692))
  * [winpython](https://pypi.org/project/winpython) 10.7.20240908 → 11.2.20241228 (WinPython distribution tools, including WPPM)
  * [wordcloud](https://pypi.org/project/wordcloud) 1.9.3 → 1.9.4 (A little word cloud generator)
  * [xarray](https://pypi.org/project/xarray) 2024.7.0 → 2024.11.0 (N-D labeled arrays and datasets in Python)
  * [yarl](https://pypi.org/project/yarl) 1.7.2 → 1.18.3 (Yet another URL library)

Removed packages:

  * [dirty_cat](https://pypi.org/project/dirty_cat) 0.4.1 (Machine learning with dirty categories.)
  * [email_validator](https://pypi.org/project/email_validator) 2.2.0 (A robust email address syntax and deliverability validation library.)
  * [fastapi_cli](https://pypi.org/project/fastapi_cli) 0.0.4 (Run and manage FastAPI apps from the command line with FastAPI CLI. 🚀)
  * [httptools](https://pypi.org/project/httptools) 0.6.1 (A collection of framework independent HTTP protocol utils.)
  * [msvc_runtime](https://pypi.org/project/msvc_runtime) 14.40.33807 (Install the Microsoft™ Visual C++™ runtime DLLs to the sys.prefix and Scripts directories)
  * [pmdarima](https://pypi.org/project/pmdarima) 2.0.4 (Python's forecast::auto.arima equivalent)
  * [shellingham](https://pypi.org/project/shellingham) 1.5.0.post1 (Tool to Detect Surrounding Shell)
  * [swifter](https://pypi.org/project/swifter) 1.3.4 (A package which efficiently applies any function to a pandas dataframe or series in the fastest available manner)
  * [tbats](https://pypi.org/project/tbats) 1.1.0 (BATS and TBATS for time series forecasting)
  * [typer](https://pypi.org/project/typer) 0.12.3 (Typer, build great CLIs. Easy to code. Based on Python type hints.)
  * [watchfiles](https://pypi.org/project/watchfiles) 0.21.0 (Simple, modern and high performance file watching and code reload in python.)


</details>
* * *
