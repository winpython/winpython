# wppm — Manage your Python packages

`wppm` is a complement to `pip`, for **any** Python environment (it was born in
[WinPython](https://winpython.github.io/), the portable Windows distribution, but does
not require it). Keep using `pip` to install and remove things — use `wppm` to *see*
what is actually there.

```console
pip install wppm
```

## Global navigation commands

**What packages are there?** package version and summary

```console
$ wppm -ls
Package            Version        Summary
__________________ ______________ ______________________________________________________________________
build              1.5.0          A simple, correct Python build frontend
certifi            2026.6.17      Python package for providing Mozilla's CA Bundle.
charset-normalizer 3.4.9          The Real First Universal Charset Detector. Open, modern and actively m
...
```

**What did I actually ask for?** Nothing in an environment records which packages you
chose and which merely came along. `-tl` keeps only the entries nothing else pulls in:

```console
$ wppm -tl
build
duckdb
flake8
flit
pandas
pillow
pipdeptree
pytest
PyYAML
wppm
# 32 entries -> 10 kept, 22 already pulled in
```

**What are the dependencies?**

```console
$ wppm -tl -p
build==1.5.0 ,
    colorama==0.4.6 ;os_name==nt
    packaging==26.2 >=24.0
    pyproject-hooks==1.2.0
duckdb==1.5.4
flake8==7.1.1 ,
    mccabe==0.7.0 (<0.8.0,>=0.7.0)
...
```

## Navigation per package(s)

**What does a package need?** `-p` walks downwards, `-l` says how many levels:

```console
$ wppm -p pandas -l2
pandas==3.0.3 ,
    numpy==2.4.6 >=2.3.3;python_version>=3.14
    python-dateutil==2.9.0.post0 >=2.8.2,
        six==1.17.0 >=1.5
    tzdata==2025.3 ;sys_platform==win32
```

**What packages are upgrade constrained?** `-r` walks upwards, and `!` keeps only the packages
that *pin or cap* the one you name, `.` means to look for *every package*:

```console
$ wppm -r  ".!"
charset-normalizer==3.4.9 ,
    requests==2.34.2 [requires: charset-normalizer<4,>=2]
idna==3.18 ,
    requests==2.34.2 [requires: idna<4,>=2.5]
...
```

> Quoting: `!` and `[` are shell metacharacters in POSIX shells, so quote any argument
> containing them (`wppm -r "pluggy!"`). In `cmd.exe` the quotes are optional.


## Package [Extras] analysis

use brackets to specify extra(s) `[extra]`, `[.]` means *every extra*,
and `!` narrows the answer to what is **missing** — `==?` marks a requirement that is
not installed:

**What am I missing, per flit extra?**
```console
$ wppm -p "flit![.]"
flit[doc]==3.12.0 ,
    pygments-github-lexers==? ;extra==doc
    sphinx==? ;extra==doc
    sphinxcontrib-github-alt==? ;extra==doc
flit[test]==3.12.0 ,
    pytest-cov==? ;extra==test
    responses==? ;extra==test
    testpath==? ;extra==test
    tomli==? ;extra==test
```

**Which package[extra] may want numpy?**

```console
$ wppm -r "numpy[.]"
numpy==2.4.6 ,
    pandas==3.0.3 [requires: numpy>=2.3.3;python_version>=3.14]
numpy[all]==2.4.6 ,
    duckdb[all]==1.5.4 [requires: numpy;extra==all]
```

## Pruning a requirements file

Given a file, `-tl` answers for that file's entries. Plainly, it prints the pruned list
and nothing else — so the output is a reduced requirement file, `-v` will include the
reason for each pruned package:

```console
$ wppm requirements.txt -tl > requirements_new.txt
# 160 entries -> 112 kept, 48 already pulled in
# 8 repeated, collapsed: brotli, openai, pympler, pytest, python-barcode, ...
```

```console
$ wppm requirements.txt -tl -v
# requirements.txt, sorted, 2026-08-13 19:22:43
# 160 entries -> 112 kept, 48 already pulled in
...
#numpy  # <- baresql, clarabel, cvxpy, dask[array,dataframe,diagnostics], datashader, ...
#scikit-learn  # <- imbalanced-learn, mlxtend, prince, skrub, umap-learn
#whatthepatch  # <- spyder
```

## Answers a script can read

`-p`, `-r`, `-tl`, `-ls` and `-md` all accept `-j` / `--json`, so the same answers can
gate a CI job or be diffed between two environments:

```console
$ wppm -p myapp -j | python -c "import sys,json; s=json.load(sys.stdin); [s.extend(n['depends']) for n in s]; sys.exit(1 if any(not n['installed'] for n in s) else 0)"
```

Better still, skip the terminal: the tree engine is a plain importable module — no
subprocess, no parsing of terminal output.

```python
>>> from wppm import piptree
>>> pip = piptree.PipData()             # or PipData(target=r"D:\WPy64\python")
>>> print(pip.down("pandas", "mysql"))
pandas[mysql]==3.0.3 ,
    numpy==2.4.6 >=2.3.3;python_version>=3.14
    pymysql==? >=1.1.1;extra==mysql
    python-dateutil==2.9.0.post0 >=2.8.2,
        six==1.17.0 >=1.5
    sqlalchemy==? >=2.0.36;extra==mysql
    tzdata==2025.3 ;sys_platform==win32
>>> pip.summary("pandas")
'Powerful data structures for data analysis, time series, and statistics'
```

`down()` and `up()` return indented text by default, or a JSON string with
`format="json"`; both take `top_level=True` to start from the top-level entries.
`top_level()` itself returns plain data — `kept`, and `dropped` mapping each dropped
entry to whatever pulls it in:

```python
>>> pip.top_level()["kept"]
['build', 'duckdb', 'flake8', 'flit', 'pandas', 'pillow', 'pipdeptree', 'pytest', 'PyYAML', 'wppm']
>>> pip.top_level(["pandas", "numpy", "requests[socks]", "pytest"])["dropped"]
{'numpy': ['pandas']}
```

## Environments you have not installed anything into

`-t` points `wppm` at *another* Python distribution, and `-ws` at a plain directory of
wheels — so you can inspect a portable distribution, or an offline bundle, without
installing it first:

```console
$ wppm -p "pandas[.]" -t D:\WPy64\python
$ wppm -ls -ws .\wheelhouse\included.wheels --json
```

With `-ws` the facts come from the wheelhouse rather than an installation, so a
requirements list can be pruned before anything is built; where several versions of a
package are present, the newest one answers.

Beyond inspection, `wppm` installs from a wheelhouse or a `pylock.toml` (`-i`, `-ws`,
`-wd`), emits a one-document environment manifest — distribution, tools, packages,
wheelhouse — as Markdown or JSON (`-md`, a lightweight SBOM), and does portability
housekeeping: on any Windows Python, `--movable` / `--fix` rewrite the `Scripts\`
launchers and shebangs between relative and absolute paths, so a directory can be moved
(or pinned back down) without breaking its entry points.

`--register` / `--unregister` associate file extensions, icons, context menu and start
menu entries with the target Python. Each distribution gets its own start menu folder,
so registering one never disturbs another — but note that the target is declared under
the `WinPython` PEP-514 vendor key.

`wppm -h` lists every option.

## Links

- Source code: <https://github.com/winpython/winpython>
- Issues and feature requests: <https://github.com/winpython/winpython/issues>
- Discussions: <https://github.com/winpython/winpython/discussions>
- WinPython distribution: <https://winpython.github.io/>
