# -*- coding: utf-8 -*-
"""
This script provides functionality to inspect and display package dependencies
in a Python environment, including both downward and upward dependencies.
Requires Python 3.8+ due to importlib.metadata.
"""

import json
import sys
import re
import platform
import os
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Union
from pip._vendor.packaging.markers import Marker, InvalidMarker
from importlib.metadata import Distribution, distributions
from pathlib import Path

def normalize(name: str) -> str:
    """Normalize package name according to PEP 503."""
    return re.sub(r"[-_.]+", "-", name).lower()

def sum_up(text: str, max_length: int = 144, stop_at: str = ". ") -> str:
    """
    Summarize text to fit within max_length characters, ending at the last complete sentence if possible.

    :param text: The text to summarize
    :param max_length: Maximum length for summary
    :param stop_at: String to stop summarization at
    :return: Summarized text
    """
    summary = (text + os.linesep).splitlines()[0]
    if len(summary) > max_length and len(stop_at) > 1:
        summary = (summary + stop_at).split(stop_at)[0]
    if len(summary) > max_length:
        summary = summary[:max_length]
    return summary

class PipData:
    """
    Wrapper around Distribution.discover() or Distribution.distributions() to manage package metadata.
    """

    def __init__(self, target: Optional[str] = None):
        self.distro: Dict[str, Dict] = {}
        self.raw: Dict[str, Dict] = {}
        self.environment = self._get_environment()

        search_path = target or sys.executable

        if sys.executable == search_path:
            packages = Distribution.discover()
        else:
            packages = distributions(path=[str(Path(search_path).parent / 'lib' / 'site-packages')])

        for package in packages:
            self._process_package(package)

        # On a second pass, complement dependencies in reverse mode with 'wanted-per':
        self._populate_reverse_dependencies()

    def _get_environment(self) -> Dict[str, str]:
        """
        Collect environment details for dependency evaluation.

        :return: Dictionary containing system and Python environment information
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

    def _process_package(self, package: Distribution) -> None:
        """Process package metadata and store it in the distro dictionary."""
        meta = package.metadata
        name = meta['Name']
        version = package.version
        key = normalize(name)
        self.raw[key] = meta

        self.distro[key] = {
            "name": name,
            "version": version,
            "summary": meta.get("Summary", ""),
            "requires_dist": self._get_requires(package),
            "reverse_dependencies": [],
            "description": meta.get("Description", ""),
            "provides": self._get_provides(package),
            "provided": {'': None}  # Placeholder for extras provided by this package
        }

    def _get_requires(self, package: Distribution) -> List[Dict[str, str]]:
        """Extract and normalize requirements for a package."""
        #     requires =  list of dict with 1 level need downward
        #             req_key = package_key requires
        #             req_extra = extra branch needed of the package_key ('all' or '')
        #             req_version = version needed
        #             req_marker = marker of the requirement (if any)
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
                req_nameextra = normalize(re.split(r" |;|==|!|>|<", req_nameextra + ";")[0])
                req_key = normalize((req_nameextra + "[").split("[")[0])
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
        """Get the list of extras provided by this package."""
        provides = {'': None}
        if package.requires:
            for req in package.requires:
                req_marker = (req + ";").split(";")[1]
                if 'extra == ' in req_marker:
                    remove_list = {ord("'"): None, ord('"'): None}
                    provides[req_marker.split('extra == ')[1].translate(remove_list)] = None
        return provides

    def _populate_reverse_dependencies(self) -> None:
        """Add reverse dependencies to each package."""
        # - get all downward links in 'requires_dist' of each package
        # - feed the required packages 'reverse_dependencies' as a reverse dict of dict
        #        contains =
        #             req_key = upstream package_key
        #             req_version = downstream package version wanted
        #             req_extra = extra option of the demanding package that wants this dependancy
        #             req_marker = marker of the downstream package requirement (if any)
        for package in self.distro:
            for requirement in self.distro[package]["requires_dist"]:
                if requirement["req_key"] in self.distro:
                    want_add = {
                        "req_key": package,
                        "req_version": requirement["req_version"],
                        "req_extra": requirement["req_extra"],
                    }
                    if "req_marker" in requirement:
                        want_add["req_marker"] = requirement["req_marker"]
                        if 'extra == ' in requirement["req_marker"]:
                            remove_list = {ord("'"): None, ord('"'): None}
                            self.distro[requirement["req_key"]]["provided"][requirement["req_marker"].split('extra == ')[1].translate(remove_list)] = None
                    self.distro[requirement["req_key"]]["reverse_dependencies"].append(want_add)

    def _get_dependency_tree(self, package_name: str, extra: str = "", version_req: str = "", depth: int = 20, path: Optional[List[str]] = None, verbose: bool = False, upward: bool = False) -> List[List[str]]:
        """Recursive function to build dependency tree."""
        path = path or []
        extras = extra.split(",")
        package_key = normalize(package_name)
        ret_all = []
        #pe = normalize(f'{package_key}[{extras}]')
        if package_key + "[" + extra + "]" in path:
            print("cycle!", "->".join(path + [package_key + "[" + extra + "]"]))
            return []  # Return empty list to avoid further recursion

        package_data = self.distro.get(package_key)
        if package_data and len(path) <= depth:
            for extra in extras:
                environment = {"extra": extra, **self.environment}
                summary = f'  {package_data["summary"]}' if verbose else ''
                base_name = f'{package_name}[{extra}]' if extra else package_name
                ret = [f'{base_name}=={package_data["version"]} {version_req}{summary}']

                dependencies = package_data["requires_dist"] if not upward else package_data["reverse_dependencies"]

                for dependency in dependencies:
                    if dependency["req_key"] in self.distro:
                        if not dependency.get("req_marker") or Marker(dependency["req_marker"]).evaluate(environment=environment):
                            next_path = path + [base_name]
                            if upward:
                                up_req = (dependency.get("req_marker", "").split('extra == ')+[""])[1].strip("'\"")
                                # 2024-06-30 example of langchain <- numpy. pip.distro['numpy']['reverse_dependencies'] has:
                                # {'req_key': 'langchain', 'req_version': '(>=1,<2)',  'req_extra': '',  'req_marker': ' python_version < "3.12"'},
                                # {'req_key': 'langchain',  'req_version': '(>=1.26.0,<2.0.0)', 'req_extra': '', 'req_marker': ' python_version >= "3.12"'}
                                # must be no extra dependancy, optionnal extra in the package, or provided extra per upper packages 
                                if dependency["req_key"] in self.distro and dependency["req_key"]+"["+up_req+"]" not in path:  # avoids circular links on dask[array]
                                 if (not dependency.get("req_marker") and extra =="") or (extra !="" and extra==up_req and dependency["req_key"]!=package_key)  or (extra !="" and "req_marker" in dependency and extra+',' in dependency["req_extra"]+',' #bingo1346 contourpy[test-no-images]
                                    or "req_marker" in dependency and extra+',' in dependency["req_extra"]+','  and Marker(dependency["req_marker"]).evaluate(environment=environment)
                                    ):
                                    ret += self._get_dependency_tree(
                                        dependency["req_key"],
                                        up_req,  # pydask[array] going upwards will look for pydask[dataframe]
                                        f"[requires: {package_name}"
                                        + (
                                            "[" + dependency["req_extra"] + "]"
                                            if dependency["req_extra"] != ""
                                            else ""
                                        )
                                        + f'{dependency["req_version"]}]',
                                        depth,
                                        next_path,
                                        verbose=verbose,
                                        upward=upward,
                                    )
                            else:
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
        """Print the downward requirements for the package or all packages."""
        if pp == ".":
            results = [self.down(one_pp, extra, depth, indent, version_req, verbose=verbose) for one_pp in sorted(self.distro)]
            return '\n'.join(filter(None, results))

        if extra == ".":
            if pp in self.distro:
                results = [self.down(pp, one_extra, depth, indent, version_req, verbose=verbose)
                           for one_extra in sorted(self.distro[pp]["provides"])]
                return '\n'.join(filter(None, results))
            return "" # Handle cases where extra is "." and package_name is not found.

        if pp not in self.distro:
            return "" # Handle cases where package_name is not found.

        rawtext = json.dumps(self._get_dependency_tree(pp, extra, version_req, depth, verbose=verbose), indent=indent)
        lines = [l for l in rawtext.split("\n") if len(l.strip()) > 2]
        return "\n".join(lines).replace('"', "")

    def up(self, pp: str, extra: str = "", depth: int = 20, indent: int = 5, version_req: str = "", verbose: bool = False) -> str:
        """Print the upward needs for the package."""
        if pp == ".":
            results = [self.up(one_pp, extra, depth, indent, version_req, verbose) for one_pp in sorted(self.distro)]
            return '\n'.join(filter(None, results))

        if extra == ".":
            if pp in self.distro:
                extras = set(self.distro[pp]["provided"]).union(set(self.distro[pp]["provides"]))
                results = [self.up(pp, one_extra, depth, indent, version_req, verbose=verbose) for one_extra in sorted(extras)]
                return '\n'.join(filter(None, results))
            return ""

        if pp not in self.distro:
            return ""

        rawtext = json.dumps(self._get_dependency_tree(pp, extra, version_req, depth, verbose=verbose, upward=True), indent=indent)
        lines = [l for l in rawtext.split("\n") if len(l.strip()) > 2]
        return "\n".join(filter(None, lines)).replace('"', "")

    def description(self, pp: str) -> None:
        """Return description of the package."""
        if pp in self.distro:
            return print("\n".join(self.distro[pp]["description"].split(r"\n")))
    
    def summary(self, pp):
        """Return summary of the package."""
        if pp in self.distro:
            return self.distro[pp]["summary"]
        return ""

    def pip_list(self, full: bool = False, max_length: int = 144) -> List[Tuple[str, Union[str, Tuple[str, str]]]]:
        """List installed packages similar to pip list."""
        if full:
            return [(p, self.distro[p]["version"], sum_up(self.distro[p]["summary"], max_length)) for p in sorted(self.distro)]
        else:
            return [(p, sum_up(self.distro[p]["version"], max_length)) for p in sorted(self.distro)]
