# -*- coding: utf-8 -*-
# require python 3.8+ because of importlib.metadata
# revamped via github/gpt-4o free then gemini flash 2 free
import json
import sys
import re
import platform
import os
from collections import OrderedDict
from pip._vendor.packaging.markers import Marker, InvalidMarker
from importlib.metadata import Distribution, distributions
from pathlib import Path


def normalize(name):
    """Normalize package name according to PEP 503."""
    return re.sub(r"[-_.]+", "-", name).lower()

def sum_up(text, max_length=144, stop_at=". "):
    """Summarize text to a single line of max_length characters."""
    summary = (text + os.linesep).splitlines()[0]
    if len(summary) > max_length and len(stop_at) > 1:
        summary = (summary + stop_at).split(stop_at)[0]
    if len(summary) > max_length:
        summary = summary[:max_length]
    return summary


class pipdata:
    """Wrapper around Distribution.discover() or Distribution.distributions()"""

    def __init__(self, target=None):

        # create a distro{} dict of Packages
        #  key = normalised package name
        #     string_elements = 'name', 'version', 'summary'
        #     requires =  list of dict with 1 level need downward
        #             req_key = package_key requires
        #             req_extra = extra branch needed of the package_key ('all' or '')
        #             req_version = version needed
        #             req_marker = marker of the requirement (if any)

        self.distro = {}
        self.raw = {}
        self.environment = self._get_environment()

        search_path = target or sys.executable 

        if sys.executable==search_path:
            # self-Distro inspection case (use all packages reachable per sys.path I presume )
            packages=Distribution.discover()
        else:
            # not self-Distro inspection case , look at site-packages only)
            packages=distributions(path=[str(Path(search_path).parent /'lib'/'site-packages'),])  


        for package in packages:
            self._process_package(package)

        # On a second pass, complement dependancies in reverse mode with 'wanted-per':
        self._populate_reverse_dependencies()

    def _get_environment(self):
        """Get the current environment details."""
        return {
            "implementation_name": sys.implementation.name,
            "implementation_version": "{0.major}.{0.minor}.{0.micro}".format(sys.implementation.version),
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

    def _process_package(self, package):
        """Process a single package and add it to the distro dictionary."""
        meta = package.metadata
        name = meta['Name']
        version = package.version
        key = normalize(name)
        self.raw[key] = meta
        provided = {'': None}
 
        requires = self._get_requires(package)
        provides = self._get_provides(package)

        self.distro[key] = {
                "name": name,
                "version": version,
                "summary": meta.get("Summary", ""),
                "requires_dist": requires,
                "wanted_per": [],
                "description": meta.get("Description", ""),
                "provides": provides, 
                "provided": provided,  # being extras from other packages: 'test' for pytest because dask['test'] wants pytest
        }

    def _get_requires(self, package):
        """Get the requirements of a package."""
        requires = []
        replacements = str.maketrans({" ": " ", "[": "", "]": "", "'": "", '"': ""}) # space not ' or '
        further_replacements=((' == ', '=='),('= ', '='), (' !=', '!='), (' ~=', '~='),
                              (' <', '<'),('< ', '<'), (' >', '>'),  ('> ', '>'),
                              ('; ', ';'), (' ;', ';'), ('( ', '('),
                              (' and (',' andZZZZZ('), (' (', '('), (' andZZZZZ(',' and (' ))

        if package.requires:
            for req in package.requires:
                # req_nameextra is "python-jose[cryptography]"
                #  from fastapi "python-jose[cryptography]<4.0.0,>=3.3.0
                # req_nameextra is "google-cloud-storage"
                #   from "google-cloud-storage (<2.0.0,>=1.26.0)
                req_nameextra, req_marker = (req + ";").split(";")[:2]
                req_nameextra = normalize(re.split(" |;|==|!|>|<", req_nameextra+";")[0])
                req_key = normalize((req_nameextra + "[").split("[")[0])
                req_key_extra = req_nameextra[len(req_key) + 1:].split("]")[0]
                req_version = req[len(req_nameextra):].translate(replacements)
                for other in further_replacements: # before we stop this cosmetic...
                    req_version = req_version.replace(*other)
                req_add = {
                    "req_key": req_key,
                    "req_version": req_version,
                    "req_extra": req_key_extra,
                }
                if not req_marker == "":
                    req_add["req_marker"] = req_marker
                requires.append(req_add)
        return requires

    def _get_provides(self, package):
        """Get the extended list of dependant packages, from extra options."""
        # 'array' is an added dependancy package of dask, if you install dask['array']
        provides = {'': None}
        if package.requires:
            for req in package.requires:
                req_marker = (req + ";").split(";")[1]
                if 'extra == ' in req_marker:
                    remove_list = {ord("'"): None, ord('"'): None}
                    provides[req_marker.split('extra == ')[1].translate(remove_list)] = None
        return provides

    def _populate_reverse_dependencies(self):
        """Populate the wanted_per field for each package."""
        # - get all downward links in 'requires_dist' of each package
        # - feed the required packages 'wanted_per' as a reverse dict of dict
        #        contains =
        #             req_key = upstream package_key
        #             req_version = downstream package version wanted
        #             req_extra = extra option of the demanding package that wants this dependancy
        #             req_marker = marker of the downstream package requirement (if any)
        for p in self.distro:
            for r in self.distro[p]["requires_dist"]:
                if r["req_key"] in self.distro:
                    want_add = {
                        "req_key": p,
                        "req_version": r["req_version"],
                        "req_extra": r["req_extra"],
                    }
                    if "req_marker" in r:
                        want_add["req_marker"] = r["req_marker"]  # req_key_extra

                        # provided = extras in upper packages that triggers the need for this package,
                        #             like 'pandas[test]->Pytest', so 'test' in distro['pytest']['provided']['test']
                        #             corner-cases: 'dask[dataframe]' -> dask[array]'
                        #                           'dask-image ->dask[array]

                        if 'extra == ' in r["req_marker"]:
                            remove_list = {ord("'"):None, ord('"'):None}
                            self.distro[r["req_key"]]["provided"][r["req_marker"].split('extra == ')[1].translate(remove_list)] = None
                    self.distro[r["req_key"]]["wanted_per"].append(want_add)

    def _get_dependency_tree(self, package_name, extra="", version_req="", depth=20, path=None, verbose=False, upward=False):
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

                dependencies = package_data["requires_dist"] if not upward else package_data["wanted_per"]

                for dependency in dependencies:
                    if dependency["req_key"] in self.distro:
                        if not dependency.get("req_marker") or Marker(dependency["req_marker"]).evaluate(environment=environment):
                            next_path = path + [base_name]
                            if upward:
                                up_req = (dependency.get("req_marker", "").split('extra == ')+[""])[1].strip("'\"")
                                # 2024-06-30 example of langchain <- numpy. pip.distro['numpy']['wanted_per'] has:
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

    def down(self, pp="", extra="", depth=20, indent=5, version_req="", verbose=False):
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

    def up(self, pp, extra="", depth=20, indent=5, version_req="", verbose=False):
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
        return '\n'.join(filter(None, lines)).replace('"', "")

    def description(self, pp):
        """Return description of the package."""
        if pp in self.distro:
            return print("\n".join(self.distro[pp]["description"].split(r"\n")))
    
    def summary(self, pp):
        """Return summary of the package."""
        if pp in self.distro:
            return  self.distro[pp]["summary"]

    def pip_list(self, full=False, max_length=144):
        """List installed packages similar to pip list."""
        if full:
            return [(p, self.distro[p]["version"], sum_up(self.distro[p]["summary"]), max_length) for p in sorted(self.distro)]
        else:
            return [(p, sum_up(self.distro[p]["version"], max_length)) for p in sorted(self.distro)]

