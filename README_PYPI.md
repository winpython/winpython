# wppm — the dependency questions `pip` won't answer

`wppm` is a small companion to `pip`, for **any** Python environment (it was born in
[WinPython](https://winpython.github.io/), the portable Windows distribution, but does
not require it). Keep using `pip` to install and remove things — use `wppm` to *see*
what is actually there.

```console
pip install wppm
```

## Which extras of a package are actually usable here?

You installed `flit`. Its `[doc]` and `[test]` extras promise more. What is missing?

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

`[.]` means *every extra*, `!` means *only show what is missing*, and `==?` marks a
requirement that is not installed. Extras with nothing missing are simply not printed —
so an empty answer means "everything this package offers is ready to use".

Drop the `!` to see the whole picture instead, installed versions included:

```console
$ wppm -p "requests[.]" -l1
requests==2.34.2 ,
    certifi==2026.6.17 >=2023.5.7
    charset-normalizer==3.4.9 <4,>=2
    idna==3.18 <4,>=2.5
    urllib3==2.7.0 <3,>=1.26
requests[socks]==2.34.2 ,
    certifi==2026.6.17 >=2023.5.7
    charset-normalizer==3.4.9 <4,>=2
    idna==3.18 <4,>=2.5
    pysocks==? !=1.5.7,>=1.5.6;extra==socks
    urllib3==2.7.0 <3,>=1.26
requests[use-chardet-on-py3]==2.34.2 ,
    certifi==2026.6.17 >=2023.5.7
    chardet==? <8,>=3.0.2;extra==use-chardet-on-py3
    charset-normalizer==3.4.9 <4,>=2
    idna==3.18 <4,>=2.5
    urllib3==2.7.0 <3,>=1.26
```

## Who pulls in `pytest`, and through which extra?

The reverse direction, `-r`, is extras-aware too — it tells you *why* something is in
your environment, down to the extra that asked for it:

```console
$ wppm -r "pytest[.]"
pytest==9.0.3
pytest[all]==9.0.3 ,
    idna[all]==3.18 [requires: pytest>=8.3.2;extra==all]
    pandas[all]==3.0.3 [requires: pytest>=8.3.4;extra==all]
pytest[dev]==9.0.3
pytest[test]==9.0.3 ,
    flit[test]==3.12.0 [requires: pytest>=2.7.3;extra==test]
    pandas[test]==3.0.3 [requires: pytest>=8.3.4;extra==test]
pytest[testing]==9.0.3 ,
    pluggy[testing]==1.6.0 [requires: pytest;extra==testing]
pytest[tests]==9.0.3 ,
    pillow[tests]==12.3.0 [requires: pytest;extra==tests]
```

## What will break when I upgrade?

With `-r`, the `!` filter keeps only the packages that *pin or cap* the one you name —
the handful that will actually fight your next upgrade, instead of the long list of
packages that merely depend on it:

```console
$ wppm -r "pluggy!"
pluggy==1.6.0 ,
    pytest==9.0.3 [requires: pluggy<2,>=1.5]
```

An empty answer here is good news: nothing constrains it, upgrade away.

And the whole constraint web of an environment — every package, every extra, nine
levels deep — is one command:

```console
$ wppm -p ".[.]" -l9
```

## What did you actually ask for?

`-p` and `-r` answer for one package. `--roots` answers for a whole list: it keeps only
the entries nothing else in that list already pulls in, sorted, and comments out the rest
with the reason.

```console
$ wppm requirements_slim.txt --roots -v -t D:\WPy64\python
# requirements_slim.txt, sorted, with every entry
# another one already pulls in commented out: 160 entries -> 112.

...
#numpy  # <- baresql, clarabel, cvxpy, dask[array,dataframe,diagnostics], datashader, ...
#scikit-learn  # <- imbalanced-learn, mlxtend, prince, skrub, umap-learn
#whatthepatch  # <- spyder
```

Dropped entries come back as comments, so re-asking for one is uncommenting it, and the
notes in the source file are carried over. With no file, the question becomes "of
everything installed here, what did anything actually ask for?":

```console
$ wppm --roots -t D:\WPy64\python
```

An optional dependency only counts where its extra is asked for, and a mutual pair keeps
both members -- dropping either would take the other with it. With `-ws` the facts come
from a wheelhouse instead of an installation, so a list can be pruned before anything is
built; where the wheelhouse holds several versions of a package, the newest one answers.

## Everything is available as JSON

Any of `-p`, `-r`, `-ls`, `-md` accepts `-j` / `--json`, so the same answers can gate a
CI job or be diffed between two environments:

```console
$ wppm -p pluggy -j
[
    {
        "package": "pluggy",
        "extra": "",
        "version": "1.6.0",
        "installed": true,
        "constraint": "",
        "depends": []
    }
]
```

```console
$ wppm -p myapp -j | python -c "import sys,json; s=json.load(sys.stdin); [s.extend(n['depends']) for n in s]; sys.exit(1 if any(not n['installed'] for n in s) else 0)"
```

## Or use it from Python

The tree engine is a plain importable module — no subprocess, no parsing of terminal
output. `down()` walks dependencies, `up()` walks them backwards, and both return
indented text by default or a JSON string with `format="json"`:

```python
import json
from wppm import piptree

pip = piptree.PipData()                 # or PipData(target=r"D:\WPy64\python")

tree = json.loads(pip.down("pandas", "mysql", format="json"))
missing = [d["package"] for d in tree[0]["depends"] if not d["installed"]]
print(f"pandas[mysql] needs: {missing}")
```

```console
pandas[mysql] needs: ['pymysql', 'sqlalchemy']
```

```python
>>> print(pip.up("pluggy!"))     # who caps pluggy?
pluggy==1.6.0 ,
    pytest==9.0.3 [requires: pluggy<2,>=1.5]
>>> pip.summary("pandas")
'Powerful data structures for data analysis, time series, and statistics'
```

## It also works on environments you have not installed anything into

`-t` points `wppm` at *another* Python distribution, and `-ws` at a plain directory of
wheels — so you can inspect a portable distribution, or an offline bundle, without
installing it first:

```console
$ wppm -ls -ws .\wheelhouse\included.wheels --json
$ wppm -p "pandas[.]" -t D:\WPy64\python
```

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

## Compared with `pipdeptree`

`wppm` adds per-`[extra]` granularity in **both** directions, the `!` filter (missing
dependencies forward, constraining dependencies backward), and the ability to inspect
another environment (`-t`) or a bare directory of wheels (`-ws`) without installing
anything into it.

> Quoting: `!` and `[` are shell metacharacters in POSIX shells, so quote the argument
> (`wppm -p "flit![.]"`). In `cmd.exe` the quotes are optional.

## Command line

```text
usage: wppm [-h] [-v] [--register] [--unregister] [--fix] [--movable]
            [-ws WHEELSOURCE] [-wd WHEELDRAIN] [-ls] [-lsa] [-md] [-p] [-r]
            [-roots] [-l LEVELS] [-j] [-t TARGET] [-i] [-u]
            [package(s) or lockfile ...]

WinPython Package Manager: handle a Python distribution (WinPython or not) and its packages (17.10.20260808)

positional arguments:
  package(s) or lockfile
                        optional package names, wheels, or lockfile

options:
  -h, --help            show this help message and exit
  -v, --verbose         show more details on packages and actions
  --register            Register the target Python in Windows (file extensions, icons, context menu, start menu), under the 'WinPython' PEP-514 vendor key
  --unregister          Unregister the target Python from Windows: de-associate file extensions, icons and context menu, and remove its start menu folder
  --fix                 make the target Python use absolute (fixed) paths in launchers and shebangs
  --movable             make the target Python (any Windows Python) movable/portable: relative paths in launchers and shebangs
  -ws WHEELSOURCE       wheels location, ('.' = WheelHouse): wppm pylock.toml -ws source_of_wheels, wppm -ls -ws .
  -wd WHEELDRAIN        wheels destination: wppm pylock.toml -wd destination_of_wheels
  -ls, --list           list installed packages matching [optional] expression: wppm -ls, wppm -ls pand
  -lsa                  list details of packages matching [optional]  expression: wppm -lsa pandas -l1
  -md                   markdown summary of the installation
  -p                    show Package (!= missing) dependencies of the given package[option], [.]=all: wppm -p pandas[.]
  -r                    show Reverse (!= constraining) dependancies of the given package[option]: wppm -r pytest![test]
  -roots, --roots       keep only what no other entry pulls in, sorted: wppm --roots, wppm requirements.txt --roots -v
  -l LEVELS             show 'LEVELS' levels of dependencies (with -p, -r): wppm -p pandas -l1
  -j, --json            machine-readable JSON output (with -p, -r, -ls, -md, --roots): wppm -p pandas[.] -j
  -t TARGET             path to target Python distribution (default: current environment)
  -i, --install         install a given package wheel or pylock file (use pip for more features)
  -u, --uninstall       uninstall package  (use pip for more features)
```

## Links

- Source code: <https://github.com/winpython/winpython>
- Issues and feature requests: <https://github.com/winpython/winpython/issues>
- Discussions: <https://github.com/winpython/winpython/discussions>
- WinPython distribution: <https://winpython.github.io/>
