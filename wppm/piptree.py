# -*- coding: utf-8 -*-
"""
piptree.py: inspect and display Python package dependencies,
supporting both downward and upward dependency trees.
Requires Python 3.8+ due to importlib.metadata.

Keep this module free of subprocess: it must stay pure importlib.metadata +
pathlib, so it can run where no process can be spawned -- notably inside
JupyterLite/Pyodide, where piptree is known to work. The rest of wppm
(Distribution, -md, -i, -u) does spawn and is Windows-only; piptree is the
part that travels. See _get_environment() for the one place this bites.
"""

import json
import sys
import re
import platform
import os
import logging
from functools import lru_cache
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Union
try:
    from packaging.markers import Marker
    from packaging.version import Version
except  ModuleNotFoundError:
    from pip._vendor.packaging.markers import Marker
    from pip._vendor.packaging.version import Version
from importlib.metadata import Distribution, distributions
from pathlib import Path
from . import utils
from . import packagemetadata as pm 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipDataError(Exception):
    """Custom exception for PipData related errors."""
    pass

class PipData:
    """Manages package metadata and dependency relationships in a Python environment."""

    def __init__(self, target: Optional[str] = None, wheelhouse = None):
        """
        Initialize the PipData instance.

        :param target: Optional target path to search for packages
        """
        self.distro: Dict[str, Dict] = {}
        self.raw: Dict[str, Dict] = {}
        self.environment = self._get_environment()
        self._marker_evals: Dict[Tuple[str, str], bool] = {}
        self._reported_cycles: set = set()
        try:
            packages = self._get_packages(target or sys.executable, wheelhouse)
            self._process_packages(packages)
            self._populate_reverse_dependencies()
        except Exception as e:
            raise PipDataError(f"Failed to initialize package data: {str(e)}") from e

    @staticmethod
    @lru_cache(maxsize=None)
    def normalize(name: str) -> str:
        """Normalize package name per PEP 503."""
        return re.sub(r"[-_.]+", "-", name).lower()

    def _get_environment(self) -> Dict[str, str]:
        """Collect system and Python environment details, for marker evaluation.

        These describe the *running* interpreter, not `target`. So when -t points
        at another Python, markers can pick the wrong branch: a 3.13 target read
        from a 3.14 wppm resolves `python_version >= '3.14'` as true. pip_list()
        is unaffected (it evaluates no marker); down()/up() are.

        Do NOT fix this by asking the target interpreter over subprocess: this
        runs once per PipData, on the only code path that works without process
        spawning (see module docstring). Read the target's version from files
        instead -- `pyvenv.cfg` carries `version = 3.13.7` for a venv, and
        `python313.dll` at the root gives major.minor for a plain install or
        WinPython (skip the `...t.dll` free-threaded variant). Both are ordinary
        reads, and only needed when target is not the running interpreter.
        """
        return {
            "implementation_name": sys.implementation.name,
            "implementation_version": f"{sys.implementation.version.major}.{sys.implementation.version.minor}.{sys.implementation.version.micro}",
            "os_name": os.name,
            "platform_machine": platform.machine(),
            "platform_release": platform.release(),
            "platform_system": platform.system(),
            "platform_version": platform.version(),
            "python_full_version": platform.python_version(),
            "platform_python_implementation": platform.python_implementation(),
            "python_version": ".".join(platform.python_version_tuple()[:2]),
            "sys_platform": sys.platform,
        }

    def _get_packages(self, search_path: str, wheelhouse) -> List[Distribution]:
        """Retrieve installed packages from the specified path."""
        if wheelhouse:
            return self._newest_of_each(pm.get_directory_metadata(wheelhouse))
        if sys.executable == search_path:
            return pm.get_installed_metadata() #Distribution.discover()
        else:
            # get_site_packages_path resolves from the distribution root, so it copes
            # with the venv layout (python.exe in Scripts, site-packages at the root)
            return pm.get_installed_metadata(path=[utils.get_site_packages_path(search_path)])

    @staticmethod
    def _newest_of_each(packages: List) -> List:
        """One distribution per name, the highest version.

        A wheelhouse commonly holds several versions of a package; the
        environment PipData models holds one, and reading whichever the
        directory listing returned last would make the answer arbitrary.
        """
        def version_of(package):
            try:
                return Version(package.version)
            except Exception:   # a local or malformed version still sorts, just last
                return Version("0")

        newest = {}
        for package in packages:
            key = PipData.normalize(package.name)
            if key not in newest or version_of(package) > version_of(newest[key]):
                newest[key] = package
        return list(newest.values())

    def _process_packages(self, packages: List[Distribution]) -> None:
        """Process packages metadata and store them in the distro dictionary."""
        for package in packages:
            try:
                meta = package.metadata
                name = meta.get('Name')
                if not name:
                    continue
                key = self.normalize(name)
                self.raw[key] = meta
                self.distro[key] = {
                    "name": name,
                    "version": package.version,
                    "summary": meta.get("Summary", ""),
                    "requires_dist": self._get_requires(package),
                    "reverse_dependencies": [],
                    "description": meta.get("Description", ""),
                    "provides": self._get_provides(package),
                    "provided": {'': None}   # Placeholder for extras provided by this package
                }
            except Exception as e:
                logger.warning(f"Failed to process package {name}: {str(e)}", exc_info=True)

    def _get_requires(self, package: Distribution) -> List[Dict[str, str]]:
        """Extract and normalize requirements for a package."""
        requires = []
        replacements = str.maketrans({" ": " ", "[": "", "]": "", "'": "", '"': ""})
        further_replacements = [
            (' == ', '=='), ('= ', '='), (' !=', '!='), (' ~=', '~='),
            (' <', '<'), ('< ', '<'), (' >', '>'), ('> ', '>'),
            ('; ', ';'), (' ;', ';'), ('( ', '('),
            (' and (', ' andZZZZZ('), (' (', '('), (' andZZZZZ(', ' and (')
        ]

        if package.requires:
            for req in package.requires:
                req_nameextra, req_marker = (req + ";").split(";")[:2]
                req_nameextra = self.normalize(re.split(r" |;|==|!|>|<|~=", req_nameextra + ";")[0])
                req_key = self.normalize((req_nameextra + "[").split("[")[0])
                req_key_extra = req_nameextra[len(req_key) + 1:].split("]")[0]
                req_version = req[len(req_nameextra):].translate(replacements)

                for old, new in further_replacements:
                    req_version = req_version.replace(old, new)

                req_add = {
                    "req_key": req_key,
                    "req_version": req_version,
                    "req_extra": req_key_extra,
                }
                if req_marker != "":
                    req_add["req_marker"] = req_marker
                requires.append(req_add)
        return sorted(requires, key=lambda x: x["req_key"])

    def _get_provides(self, package: Distribution) -> Dict[str, None]:
        """Extract provided extras from package requirements."""
        provides = {'': None}
        if package.requires:
            for req in package.requires:
                req_marker = (req + ";").split(";")[1]
                if 'extra == ' in req_marker:
                    remove_list = {ord("'"): None, ord('"'): None}
                    provides[req_marker.split('extra == ')[1].translate(remove_list)] = None
        return provides

    def _populate_reverse_dependencies(self) -> None:
        """Populate reverse dependencies."""
        for pkg_key, pkg_data in self.distro.items():
            for req in pkg_data["requires_dist"]:
                target_key = req["req_key"]
                if target_key in self.distro:
                    rev_dep = {"req_key": pkg_key, "req_version": req["req_version"], "req_extra": req["req_extra"]}
                    if "req_marker" in req:
                        rev_dep["req_marker"] = req["req_marker"]
                        if 'extra == ' in req["req_marker"]:
                            remove_list = {ord("'"): None, ord('"'): None}
                            self.distro[target_key]["provided"][req["req_marker"].split('extra == ')[1].translate(remove_list)] = None
                    self.distro[target_key]["reverse_dependencies"].append(rev_dep)

    def _marker_true(self, marker: str, extra: str) -> bool:
        """Evaluate a requirement marker for a given extra, memoized (environment is fixed per instance)."""
        key = (marker, extra)
        result = self._marker_evals.get(key)
        if result is None:
            result = Marker(marker).evaluate(environment={"extra": extra, **self.environment})
            self._marker_evals[key] = result
        return result

    def _get_dependency_tree(self, package_name: str, extra: str = "", version_req: Union[str, Dict] = "", depth: int = 20, path: Optional[List[str]] = None, verbose: bool = False, upward: bool = False, ppend: str="") -> List[Dict]:
        """Recursive function to build dependency tree as a list of node dicts, one per requested extra."""
        path = path or []
        extras = extra.split(",")
        pkg_key = self.normalize(package_name)
        ret_all = []
        wall_hit = ""

        full_name = f"{package_name}[{extra}]" if extra else package_name
        if full_name in path:
            # report only the cycle itself (not the path leading to it), and only once:
            # the same loop reached from other roots or entered at another point is not news
            cycle = path[path.index(full_name):]
            rotation = cycle.index(min(cycle))
            canonical = tuple(cycle[rotation:] + cycle[:rotation])
            if canonical not in self._reported_cycles:
                self._reported_cycles.add(canonical)
                logger.warning(f"Cycle detected: {' -> '.join(cycle + [full_name])}")
            return []

        pkg_data = self.distro[pkg_key]
        if pkg_data and len(path) <= depth:
            for extra in extras:
                base_name = f'{package_name}[{extra}]' if extra else package_name
                node = {
                    "package": package_name,
                    "extra": extra,
                    "version": pkg_data["version"],
                    "installed": True,
                    "constraint": version_req,
                    "depends": [],
                }
                if isinstance(version_req, dict):
                    # upward annotation: which requirement of the package below brought us here
                    node["requires"] = version_req
                    node["constraint"] = (f'[requires: {version_req["package"]}'
                        + (f'[{version_req["extra"]}]' if version_req["extra"] != "" else "")
                        + f'{version_req["spec"]}]')
                if verbose:
                    node["summary"] = pkg_data["summary"]

                dependencies = pkg_data["requires_dist"] if not upward else pkg_data["reverse_dependencies"]

                for dependency in dependencies:
                    if dependency["req_key"] in self.distro:
                        next_path = path + [base_name]
                        if upward:     
                            up_req = (dependency.get("req_marker", "").split('extra == ')+[""])[1].strip("'\"")
                            if dependency["req_key"] in self.distro and dependency["req_key"]+"["+up_req+"]" not in path:
                                # upward dependancy taken if:
                                # - if extra "" demanded, and no marker from upward package: like pandas[] ==> numpy
                                # - or the extra is in the upward package, like pandas[test] ==> pytest, for 'test' extra
                                # - or an extra "array" is demanded, and indeed in the req_extra list: array,dataframe,diagnostics,distributer 
                                if (not dependency.get("req_marker") and extra == "") or \
                                   ("req_marker" in dependency and extra == up_req and \
                                    dependency["req_key"] != pkg_key and \
                                    self._marker_true(dependency["req_marker"], extra)) or \
                                   ("req_marker" in dependency and extra != "" and \
                                    extra + ',' in dependency["req_extra"] + ',' and \
                                    self._marker_true(dependency["req_marker"], up_req)):
                                    # IA risk error: # dask[array] go upwards as dask[dataframe], so {"extra": up_req} , not {"extra": extra}
                                    #tag upward limiting dependancies
                                    wall = " " if dependency["req_version"][:1] == "~" or dependency["req_version"].startswith("==") or "<" in dependency["req_version"] else ""
                                    wall_hit += wall
                                    if ppend=="" or wall==" ":
                                        node["depends"] += self._get_dependency_tree(
                                            dependency["req_key"],
                                            up_req,
                                            {"package": package_name, "extra": dependency["req_extra"], "spec": dependency["req_version"]},
                                            depth,
                                            next_path,
                                            verbose=verbose,
                                            upward=upward,
                                        )
                        elif not dependency.get("req_marker") or self._marker_true(dependency["req_marker"], extra):
                            #tag downward missing dependancies
                            wall = ""
                            if ppend=="" or wall==" ":
                                node["depends"] += self._get_dependency_tree(
                                    dependency["req_key"],
                                    dependency["req_extra"],
                                    dependency["req_version"],
                                    depth,
                                    next_path,
                                    verbose=verbose,
                                    upward=upward,
                                )
                    elif not upward and len(path) < depth and (not dependency.get("req_marker") or self._marker_true(dependency["req_marker"], extra)):
                        # not there but was required
                        wall_hit += " "
                        node["depends"].append({
                            "package": dependency["req_key"],
                            "extra": dependency["req_extra"],
                            "version": None,
                            "installed": False,
                            "constraint": dependency["req_version"],
                            "depends": [],
                        })

                ret_all.append(node)
        if ppend=="" or wall_hit != "":
            return ret_all
        else:
            return []

    @staticmethod
    def split_requirement(text: str) -> Tuple[str, List[str]]:
        """'dask[array,dataframe]>=2.0' -> ('dask', ['array', 'dataframe'])."""
        name_extras = re.split(r"[=<>~!;@ ]", text.strip(), maxsplit=1)[0]
        name, _, extras = name_extras.partition("[")
        return PipData.normalize(name), [e.strip() for e in extras.rstrip("]").split(",") if e.strip()]

    def dependency_closure(self, package: str, extra: str = "") -> set:
        """Every installed package reachable from `package[extra]`, itself excluded.

        An optional dependency counts only where its extra is asked for: a
        requirement gated on `extra == "test"` is not followed for a bare
        package, since nothing installed it on that account.
        """
        key = self.normalize(package)
        reached, seen = set(), set()
        stack = [(key, e) for e in extra.split(",") if e] + [(key, "")]
        while stack:
            pkg, pkg_extra = stack.pop()
            if (pkg, pkg_extra) in seen or pkg not in self.distro:
                continue
            seen.add((pkg, pkg_extra))
            for req in self.distro[pkg]["requires_dist"]:
                marker = req.get("req_marker")
                if marker and not self._marker_true(marker, pkg_extra):
                    continue
                if req["req_key"] in self.distro:
                    reached.add(req["req_key"])
                    stack.append((req["req_key"], req["req_extra"]))
        reached.discard(key)
        return reached

    def top_level(self, entries: Optional[List[str]] = None) -> Dict:
        """Which entries no other entry already pulls in.

        `entries` are requirement strings ("dask[array]", "numpy==2.0"); given
        none, every installed package is an entry. Returns the entries to keep
        in alphabetical order, and for each dropped one the entries that pull
        it in -- a requirements file saying what it means, rather than what a
        dependency would have installed anyway.

        A mutual pair (a needs b, b needs a) keeps both: dropping either would
        take the other with it. An entry the target has never installed cannot
        be resolved, so it is kept and reported apart.
        """
        if entries is None:
            entries = [pkg["name"] for pkg in self.distro.values()]
        asked: Dict[str, Tuple[str, List[str]]] = {}   # key -> (as written, extras)
        duplicates = []
        for text in entries:
            key, extras = self.split_requirement(text)
            if key in asked:
                duplicates.append(text)
                if len(text) <= len(asked[key][0]):
                    continue   # keep the fuller spelling: extras and pins matter
            asked[key] = (text, extras)
        reach = {key: self.dependency_closure(key, ",".join(extras)) if key in self.distro else set()
                 for key, (_, extras) in asked.items()}
        dropped = {}
        for key, (text, _) in asked.items():
            # named plainly: what pulls a package in is the package, not the
            # extras and pin the entry happened to be written with
            pullers = sorted((self.distro[other]["name"] if other in self.distro else other
                              for other in asked
                              if other != key and key in reach[other] and other not in reach[key]),
                             key=str.lower)
            if pullers:
                dropped[text] = pullers
        return {
            "kept": sorted((text for text, _ in asked.values() if text not in dropped), key=str.lower),
            "dropped": dict(sorted(dropped.items(), key=lambda item: item[0].lower())),
            "duplicates": sorted(duplicates, key=str.lower),
            "unknown": sorted((text for key, (text, _) in asked.items() if key not in self.distro), key=str.lower),
        }

    def _roots(self, pp: str, top_level: bool = False) -> List[str]:
        """Where a tree starts: the one package named, or "." for every installed one.

        `top_level` narrows "." to the entries no other installed package pulls
        in -- the same answer `top_level()` gives, used as the roots of a
        forest. The whole environment then reads as a handful of trees instead
        of one tree per package, most of them a branch of another.
        """
        if pp != ".":
            return [pp] if pp in self.distro else []
        if not top_level:
            return list(self.distro)
        return [key for key in (self.split_requirement(text)[0] for text in self.top_level()["kept"])
                if key in self.distro]

    def _node_text(self, node: Dict) -> str:
        """Render a tree node dict as its one-line text form."""
        if not node["installed"]:
            return f'{node["package"]}==? {node["constraint"]}'
        summary = f'  {node["summary"]}' if "summary" in node else ''
        base_name = f'{node["package"]}[{node["extra"]}]' if node["extra"] else node["package"]
        return f'{base_name}=={node["version"]} {node["constraint"]}{summary}'

    def _node_lines(self, node: Dict) -> List:
        """Convert a tree node dict to nested lists of text lines, for indented display."""
        ret = [self._node_text(node)]
        for child in node["depends"]:
            ret.append(self._node_lines(child))
        return ret

    def _format_tree(self, results: List[Dict], indent: int, format: str, updown: str = "down") -> str:
        """Render collected tree node dicts as indented text or JSON."""
        if format == "json":
            return json.dumps(results, indent=indent)
        rawtext = json.dumps([self._node_lines(node) for node in results], indent=indent)
        lines = [l[2*indent:] for l in rawtext.split("\n") if len(l.strip()) > 2]
        if updown == "up":
            return "\n".join(filter(None, lines)).replace('"', "")
        return "\n".join(lines).replace('"', "")

    def down(self, ppw: str = "", extra: str = "", depth: int = 20, indent: int = 4, version_req: str = "", verbose: bool = False, format: str = "text", top_level: bool = False) -> str:
        """Generate downward dependency tree, as indented text or JSON (format="json")."""
        pp = ppw[:-1] if ppw.endswith('!') else ppw
        ppend = "!" if ppw.endswith('!') else "" #show only downward missing dependancies
        ppp = self._roots(pp, top_level)
        results = []
        for p in sorted(ppp):
            if extra == ".":
                for one_extra in sorted(self.distro[p]["provides"]):
                    a =  self._get_dependency_tree(p, one_extra, version_req, depth, verbose=verbose, ppend=ppend)
                    results += a if a and (a[0]["depends"] or ppend=="") else []
            else:
                a = self._get_dependency_tree(p, extra, version_req, depth, verbose=verbose, ppend=ppend)
                results += a if a and (a[0]["depends"] or ppend=="") else []
        return self._format_tree(results, indent, format, "down")

    def up(self, ppw: str, extra: str = "", depth: int = 20, indent: int = 4, version_req: str = "", verbose: bool = False, format: str = "text", top_level: bool = False) -> str:
        """Generate upward dependency tree, as indented text or JSON (format="json")."""
        pp = ppw[:-1] if ppw.endswith('!') else ppw
        ppend = "!" if ppw.endswith('!') else "" #show only upward limiting dependancies
        ppp = self._roots(pp, top_level)
        results = []
        for p in sorted(ppp):
            if extra == ".":
                extras = set(self.distro[p]["provided"]).union(set(self.distro[p]["provides"]))
                for e in sorted(extras):
                    a = self._get_dependency_tree(p, e, version_req, depth, verbose=verbose, upward=True, ppend=ppend)
                    results += a if a and (a[0]["depends"] or ppend=="") else []
            else:
                a = self._get_dependency_tree(p, extra, version_req, depth, verbose=verbose, upward=True, ppend=ppend)
                results += a if a and (a[0]["depends"] or extra=="") else []
        return self._format_tree(results, indent, format, "up")

    def description(self, pp: str) -> None:
        """Return package description or None if not found."""
        if pp in self.distro:
            return print("\n".join(self.distro[pp]["description"].split(r"\n")))

    def summary(self, pp: str) -> str:
        """Return package summary or empty string if not found."""
        if pp in self.distro:
            return self.distro[pp]["summary"]
        return ""

    def pip_list(self, full: bool = False, max_length: int = 144) -> List[Tuple[str, Union[str, Tuple[str, str]]]]:
        """List installed packages with optional details.

        :param full: Whether to include the package version and summary
        :param max_length: The maximum length for the summary
        :return: List of tuples containing package information
        """
        pkgs = sorted(self.distro.items())
        if full:
            return [(p, d["version"], utils.sum_up(d["summary"], max_length)) for p, d in pkgs]
        return [(p, d["version"]) for p, d in pkgs]
