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
from pip._vendor.packaging.markers import Marker
from importlib.metadata import Distribution, distributions
from pathlib import Path

def normalize(name: str) -> str:
    """
    Normalize package name according to PEP 503.

    This function converts a package name to its canonical form by replacing
    any sequence of dashes, underscores, or dots with a single dash and
    converting the result to lowercase.

    :param name: The package name to normalize
    :return: The normalized package name
    """
    return re.sub(r"[-_.]+", "-", name).lower()

def sum_up(text: str, max_length: int = 144, stop_at: str = ". ") -> str:
    """
    Summarize text to fit within max_length characters, ending at the last complete sentence if possible.

    This function attempts to create a summary of the given text that fits within
    the specified maximum length. It tries to end the summary at a complete sentence
    if possible.

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

    This class provides methods to inspect and display package dependencies
    in a Python environment, including both downward and upward dependencies.
    """

    def __init__(self, target: Optional[str] = None):
        """
        Initialize the PipData instance.

        :param target: Optional target path to search for packages
        """
        self.distro: Dict[str, Dict] = {}
        self.raw: Dict[str, Dict] = {}
        self.environment = self._get_environment()

        search_path = target or sys.executable
        packages = self._get_packages(search_path)

        for package in packages:
            self._process_package(package)

        # On a second pass, complement dependencies in reverse mode with 'wanted-per':
        self._populate_reverse_dependencies()

    def _get_environment(self) -> Dict[str, str]:
        """
        Collect environment details for dependency evaluation.

        This method gathers information about the system and Python environment,
        which is used to evaluate package dependencies.

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

    def _get_packages(self, search_path: str) -> List[Distribution]:
        """
        Get the list of packages based on the search path.

        This method retrieves the list of installed packages in the specified
        search path. If the search path is the current executable, it uses
        Distribution.discover(). Otherwise, it uses distributions() with the
        specified path.

        :param search_path: Path to search for packages
        :return: List of Distribution objects
        """
        if sys.executable == search_path:
            return Distribution.discover()
        else:
            return distributions(path=[str(Path(search_path).parent / 'lib' / 'site-packages')])

    def _process_package(self, package: Distribution) -> None:
        """
        Process package metadata and store it in the distro dictionary.

        This method extracts metadata from a Distribution object and stores it
        in the distro dictionary. It also initializes the reverse dependencies
        and provided extras for the package.

        :param package: The Distribution object to process
        """
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
        """
        Extract and normalize requirements for a package.

        This method parses the requirements of a package and normalizes them
        into a list of dictionaries. Each dictionary contains the required
        package key, version, extra, and marker (if any).

        :param package: The Distribution object to extract requirements from
        :return: List of dictionaries containing normalized requirements
        """
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
        """
        Get the list of extras provided by this package.

        This method extracts the extras provided by a package from its requirements.
        It returns a dictionary where the keys are the provided extras and the values
        are None.

        :param package: The Distribution object to extract provided extras from
        :return: Dictionary containing provided extras
        """
        provides = {'': None}
        if package.requires:
            for req in package.requires:
                req_marker = (req + ";").split(";")[1]
                if 'extra == ' in req_marker:
                    remove_list = {ord("'"): None, ord('"'): None}
                    provides[req_marker.split('extra == ')[1].translate(remove_list)] = None
        return provides

    def _populate_reverse_dependencies(self) -> None:
        """
        Add reverse dependencies to each package.

        This method populates the reverse dependencies for each package in the
        distro dictionary. It iterates over the requirements of each package
        and adds the package as a reverse dependency to the required packages.
        """
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
        """
        Recursive function to build dependency tree.

        This method builds a dependency tree for the specified package. It can
        build the tree for downward dependencies (default) or upward dependencies
        (if upward is True). The tree is built recursively up to the specified
        depth.

        :param package_name: The name of the package to build the tree for
        :param extra: The extra to include in the dependency tree
        :param version_req: The version requirement for the package
        :param depth: The maximum depth of the dependency tree
        :param path: The current path in the dependency tree (used for cycle detection)
        :param verbose: Whether to include verbose output in the tree
        :param upward: Whether to build the tree for upward dependencies
        :return: List of lists containing the dependency tree
        """
        path = path or []
        extras = extra.split(",")
        package_key = normalize(package_name)
        ret_all = []

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
                        next_path = path + [base_name]
                        if upward:     
                            up_req = (dependency.get("req_marker", "").split('extra == ')+[""])[1].strip("'\"")
                            # avoids circular links on dask[array] 
                            if dependency["req_key"] in self.distro and dependency["req_key"]+"["+up_req+"]" not in path:
                                # upward dependancy taken if:
                                # - if extra "" demanded, and no marker from upward package: like pandas[] ==> numpy
                                # - or the extra is in the upward package, like pandas[test] ==> pytest, for 'test' extra
                                # - or an extra "array" is demanded, and indeed in the req_extra list: array,dataframe,diagnostics,distributer 
                                if (not dependency.get("req_marker") and extra ==""
                                )  or ("req_marker" in dependency and extra==up_req and dependency["req_key"]!=package_key and Marker(dependency["req_marker"]).evaluate(environment=environment)
                                )  or ("req_marker" in dependency and extra!="" and extra+',' in dependency["req_extra"]+',' and Marker(dependency["req_marker"]).evaluate(environment=environment|{"extra": up_req})   
                                ):
                                    ret += self._get_dependency_tree(
                                        dependency["req_key"],
                                        up_req,  # dask[array] going upwards continues as dask[dataframe]
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
        """
        Print the downward requirements for the package or all packages.

        This method prints the downward dependencies for the specified package
        or all packages if pp is ".". It uses the _get_dependency_tree method
        to build the dependency tree and formats the output as a JSON string.

        :param pp: The package name or "." to print dependencies for all packages
        :param extra: The extra to include in the dependency tree
        :param depth: The maximum depth of the dependency tree
        :param indent: The indentation level for the JSON output
        :param version_req: The version requirement for the package
        :param verbose: Whether to include verbose output in the tree
        :return: JSON string containing the downward dependencies
        """
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
        """
        Print the upward needs for the package.

        This method prints the upward dependencies for the specified package.
        It uses the _get_dependency_tree method to build the dependency tree
        and formats the output as a JSON string.

        :param pp: The package name
        :param extra: The extra to include in the dependency tree
        :param depth: The maximum depth of the dependency tree
        :param indent: The indentation level for the JSON output
        :param version_req: The version requirement for the package
        :param verbose: Whether to include verbose output in the tree
        :return: JSON string containing the upward dependencies
        """
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
        """
        Return description of the package.

        This method prints the description of the specified package.

        :param pp: The package name
        """
        if pp in self.distro:
            return print("\n".join(self.distro[pp]["description"].split(r"\n")))

    def summary(self, pp: str) -> str:
        """
        Return summary of the package.

        This method returns the summary of the specified package.

        :param pp: The package name
        :return: The summary of the package
        """
        if pp in self.distro:
            return self.distro[pp]["summary"]
        return ""

    def pip_list(self, full: bool = False, max_length: int = 144) -> List[Tuple[str, Union[str, Tuple[str, str]]]]:
        """
        List installed packages similar to pip list.

        This method lists the installed packages in a format similar to the
        output of the `pip list` command. If full is True, it includes the
        package version and summary.

        :param full: Whether to include the package version and summary
        :param max_length: The maximum length for the summary
        :return: List of tuples containing package information
        """
        if full:
            return [(p, self.distro[p]["version"], sum_up(self.distro[p]["summary"], max_length)) for p in sorted(self.distro)]
        else:
            return [(p, sum_up(self.distro[p]["version"], max_length)) for p in sorted(self.distro)]
