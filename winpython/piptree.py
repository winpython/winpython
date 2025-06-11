# -*- coding: utf-8 -*-
"""
piptree.py: inspect and display Python package dependencies,
supporting both downward and upward dependency trees.
Requires Python 3.8+ due to importlib.metadata.
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
from pip._vendor.packaging.markers import Marker
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
        """Collect system and Python environment details."""
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
            return pm.get_directory_metadata(wheelhouse)
        if sys.executable == search_path:
            return pm.get_installed_metadata() #Distribution.discover()
        else:
            return pm.get_installed_metadata(path=[str(Path(search_path).parent / 'lib' / 'site-packages')]) #distributions(path=[str(Path(search_path).parent / 'lib' / 'site-packages')])

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
        return requires

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

    def _get_dependency_tree(self, package_name: str, extra: str = "", version_req: str = "", depth: int = 20, path: Optional[List[str]] = None, verbose: bool = False, upward: bool = False) -> List[List[str]]:
        """Recursive function to build dependency tree."""
        path = path or []
        extras = extra.split(",")
        pkg_key = self.normalize(package_name)
        ret_all = []

        full_name = f"{package_name}[{extra}]" if extra else package_name
        if full_name in path:
            logger.warning(f"Cycle detected: {' -> '.join(path + [full_name])}")
            return []

        pkg_data = self.distro[pkg_key]
        if pkg_data and len(path) <= depth:
            for extra in extras:
                environment = {"extra": extra, **self.environment}
                summary = f'  {pkg_data["summary"]}' if verbose else ''
                base_name = f'{package_name}[{extra}]' if extra else package_name
                ret = [f'{base_name}=={pkg_data["version"]} {version_req}{summary}']

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
                                    Marker(dependency["req_marker"]).evaluate(environment=environment)) or \
                                   ("req_marker" in dependency and extra != "" and \
                                    extra + ',' in dependency["req_extra"] + ',' and \
                                    Marker(dependency["req_marker"]).evaluate(environment=environment | {"extra": up_req})):
                                    # IA risk error: # dask[array] go upwards as dask[dataframe], so {"extra": up_req} , not {"extra": extra}
                                    ret += self._get_dependency_tree(
                                        dependency["req_key"],
                                        up_req,
                                        f"[requires: {package_name}"
                                        + (f"[{dependency['req_extra']}]" if dependency["req_extra"] != "" else "")
                                        + f'{dependency["req_version"]}]',
                                        depth,
                                        next_path,
                                        verbose=verbose,
                                        upward=upward,
                                    )
                        elif not dependency.get("req_marker") or Marker(dependency["req_marker"]).evaluate(environment=environment):
                            ret += self._get_dependency_tree(
                                dependency["req_key"],
                                dependency["req_extra"],
                                dependency["req_version"],
                                depth,
                                next_path,
                                verbose=verbose,
                                upward=upward,
                            )

                ret_all.append(ret)
        return ret_all

    def down(self, pp: str = "", extra: str = "", depth: int = 20, indent: int = 5, version_req: str = "", verbose: bool = False) -> str:
        """Generate downward dependency tree as formatted string."""
        if pp == ".":
            results = [self.down(p, extra, depth, indent, version_req, verbose=verbose) for p in sorted(self.distro)]
            return '\n'.join(filter(None, results))

        if extra == ".":
            if pp in self.distro:
                results = [self.down(pp, one_extra, depth, indent, version_req, verbose=verbose)
                           for one_extra in sorted(self.distro[pp]["provides"])]
                return '\n'.join(filter(None, results))
            return ""

        if pp not in self.distro:
            return ""

        rawtext = json.dumps(self._get_dependency_tree(pp, extra, version_req, depth, verbose=verbose), indent=indent)
        lines = [l for l in rawtext.split("\n") if len(l.strip()) > 2]
        return "\n".join(lines).replace('"', "")

    def up(self, pp: str, extra: str = "", depth: int = 20, indent: int = 5, version_req: str = "", verbose: bool = False) -> str:
        """Generate upward dependency tree as formatted string."""
        if pp == ".":
            results = [self.up(p, extra, depth, indent, version_req, verbose) for p in sorted(self.distro)]
            return '\n'.join(filter(None, results))

        if extra == ".":
            if pp in self.distro:
                extras = set(self.distro[pp]["provided"]).union(set(self.distro[pp]["provides"]))
                results = [self.up(pp, e, depth, indent, version_req, verbose=verbose) for e in sorted(extras)]
                return '\n'.join(filter(None, results))
            return ""

        if pp not in self.distro:
            return ""

        rawtext = json.dumps(self._get_dependency_tree(pp, extra, version_req, depth, verbose=verbose, upward=True), indent=indent)
        lines = [l for l in rawtext.split("\n") if len(l.strip()) > 2]
        return "\n".join(filter(None, lines)).replace('"', "")

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
