# -*- coding: utf-8 -*-
# require python 3.8+ because of importlib.metadata
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

        target = target or sys.executable 

        if sys.executable==target:
            # self-Distro inspection case (use all packages reachable per sys.path I presume )
            packages=Distribution.discover()
        else:
            # not self-Distro inspection case , look at site-packages only)
            packages=distributions(path=[str(Path(target).parent /'lib'/'site-packages'),])  

        for package in packages:
            self._process_package(package)

        # On a second pass, complement distro in reverse mode with 'wanted-per':
        self._populate_wanted_per()

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
        #requires = self._get_requires(package)
        #provides = self._get_provides(package)


        requires = []
        provides = {'':None}

        replacements = str.maketrans({" ": "", "[": "", "]": "", "'": "", '"': ""})
        if package.requires:
            for i in package.requires:
                det = (i + ";").split(";")
                # req_nameextra is "python-jose[cryptography]"
                #  from fastapi "python-jose[cryptography]<4.0.0,>=3.3.0
                # req_nameextra is "google-cloud-storage"
                #   from "google-cloud-storage (<2.0.0,>=1.26.0)
                req_nameextra = re.split(" |;|==|!|>|<", det[0] + ";")[0]
                req_nameextra = normalize(req_nameextra)
                req_key = normalize((req_nameextra + "[").split("[")[0])
                req_key_extra = req_nameextra[len(req_key) + 1 :].split("]")[0]
                req_version = det[0][len(req_nameextra) :].translate(replacements)
                req_marker = det[1]
                if 'extra == ' in req_marker:
                    remove_list = {ord("'"):None, ord('"'):None}
                    provides[req_marker.split('extra == ')[1].translate(remove_list)] = None
                req_add = {
                    "req_key": req_key,
                    "req_version": req_version,
                    "req_extra": req_key_extra,
                }
                # add the marker of the requirement, if not nothing:
                if not req_marker == "":
                    req_add["req_marker"] = req_marker
                requires += [req_add]
        self.distro[key] = {
                "name": name,
                "version": version,
                "summary": meta.get("Summary", ""),
                "requires_dist": requires,
                "wanted_per": [],
                "description": meta.get("Description", ""),
                "provides": provides,  # extras of the package: 'array' for dask because dask['array'] defines some extra 
                "provided": provided,  # extras from other package: 'test' for pytest because dask['test'] wants pytest
        }

    def _populate_wanted_per(self):
        """Populate the wanted_per field for each package."""
        # - get all downward links in 'requires_dist' of each package
        # - feed the required packages 'wanted_per' as a reverse dict of dict
        #        contains =
        #             req_key = upstream package_key
        #             req_version = downstream package version wanted
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



    def _downraw(self, pp, extra="", version_req="", depth=20, path=[], verbose=False):
        """build a nested list of needed packages with given extra and depth"""
        envi = {"extra": extra, **self.environment}
        p = normalize(pp)

        # several extras request management: example dask[array,diagnostics] 
        extras = extra.split(",")

        ret_all = []
        if p+"["+extra+"]" in path: # for dask[complete]->dask[array,test,..]
            print("cycle!", "->".join(path + [p+"["+extra+"]"]))
        elif p in self.distro and len(path) <= depth:
            for extra in extras:  # several extras request management
                envi = {"extra": extra, **self.environment}
                summary = f'  {self.distro[p]["summary"]}' if verbose else ''
                if extra == "":
                    ret = [f'{p}=={self.distro[p]["version"]} {version_req}{summary}']
                else:
                    ret = [f'{p}[{extra}]=={self.distro[p]["version"]} {version_req}{summary}']
                for r in self.distro[p]["requires_dist"]:
                    if r["req_key"] in self.distro:
                        if "req_marker" not in r or Marker(r["req_marker"]).evaluate(
                            environment=envi
                        ):
                            ret += self._downraw(
                                r["req_key"],
                                r["req_extra"],
                                r["req_version"],
                                depth,
                                path + [p+"["+extra+"]"],
                                verbose=verbose,
                            )
                ret_all += [ret]
        return ret_all

    def _upraw(self, pp, extra="", version_req="", depth=20, path=[], verbose=False):
        """build a nested list of user packages with given extra and depth
        from direct dependancies like dask-image <--dask['array']
        or indirect like Pytest['test'] <-- pandas['test']"""

        remove_list = {ord("'"):None, ord('"'):None} # to clean-up req_extra
        envi = {"extra": extra, **self.environment}
        p = normalize(pp)
        pe = normalize(f'{pp}[{extra}]')
        ret_all = []
        if pe in path:
            print("cycle!", "->".join(path + [pe]))
        elif p in self.distro and len(path) <= depth:
            summary = f'  {self.distro[p]["summary"]}' if verbose else ''
            if extra == "":
                ret_all = [f'{p}=={self.distro[p]["version"]} {version_req}{summary}']
            elif extra in set(self.distro[p]["provided"]).union(set(self.distro[p]["provides"])): # so that -r pytest[test] gives
                ret_all = [f'{p}[{extra}]=={self.distro[p]["version"]} {version_req}{summary}']
            else:
              return []
            ret = []
            for r in self.distro[p]["wanted_per"]:
                up_req = (r["req_marker"].split('extra == ')+[""])[1].translate(remove_list) if "req_marker" in r else ""
                if r["req_key"] in self.distro and r["req_key"]+"["+up_req+"]" not in path: # avoids circular links on dask[array]
                    # 2024-06-30 example of langchain <- numpy. pip.distro['numpy']['wanted_per'] has:
                    # {'req_key': 'langchain', 'req_version': '(>=1,<2)',  'req_extra': '',  'req_marker': ' python_version < "3.12"'},
                    # {'req_key': 'langchain',  'req_version': '(>=1.26.0,<2.0.0)', 'req_extra': '', 'req_marker': ' python_version >= "3.12"'}
                    # must be no extra dependancy, optionnal extra in the package, or provided extra per upper packages 
                    if ("req_marker" not in r and extra =="") or (extra !="" and extra==up_req and r["req_key"]!=p)  or (extra !="" and "req_marker" in r and extra+',' in r["req_extra"]+',' #bingo1346 contourpy[test-no-images]
                        or "req_marker" in r and extra+',' in r["req_extra"]+','  and Marker(r["req_marker"]).evaluate(environment=envi)
                        ):
                        ret += self._upraw(
                            r["req_key"],
                            up_req, # pydask[array] going upwards will look for pydask[dataframe]
                            f"[requires: {p}"
                            + (
                                "[" + r["req_extra"] + "]"
                                if r["req_extra"] != ""
                                else ""
                            )
                            + f'{r["req_version"]}]',
                            depth,
                            path + [pe],
                            verbose=verbose,
                        )
            if not ret == []:
                ret_all += [ret]
        return ret_all

    def down(self, pp="", extra="", depth=99, indent=5, version_req="", verbose=False):
        """print the downward requirements for the package or all packages"""
        if not pp == ".":
            if not extra == ".":
                if pp in self.distro:
                    extras = [s for s in extra.split(',') if s in sorted(self.distro[pp]["provides"])]
                    if extras == []: return ''
                rawtext = json.dumps(
                    self._downraw(pp, extra, version_req, depth, verbose=verbose), indent=indent
                )
                lines = [l for l in rawtext.split("\n") if len(l.strip()) > 2]
                return ("\n".join(lines).replace('"', ""))
            else:
                if pp in self.distro:
                    r = []
                    for one_extra in sorted(self.distro[pp]["provides"]):
                        s = self.down(pp, one_extra, depth, indent, version_req, verbose=verbose)
                        if s != '': r += [s]
                    #print(r)    
                    return '\n'.join([i for i in r if i!= ''])   
        else:
            r = []
            for one_pp in sorted(self.distro):
                s = self.down(one_pp, extra, depth, indent, version_req, verbose=verbose)
                if s != '': r += [s]
            return '\n'.join([i for i in r if i!= ''])    

    def up(self, pp, extra="", depth=99, indent=5, version_req="", verbose=False):
        """print the upward needs for the package"""
        r = []
        if not pp == ".":
            if not extra == ".":
                s = self._upraw(pp, extra, version_req, depth, verbose=verbose)
                if s == []: return ''
                rawtext = json.dumps(self._upraw(pp, extra, version_req, depth, verbose=verbose), indent=indent)
                lines = [l for l in rawtext.split("\n") if len(l.strip()) > 2]
                return ("\n".join(i for i in lines if i!= '').replace('"', "") )
            else:
                if pp in self.distro:
                    r = []
                    for one_extra in sorted(set(self.distro[pp]["provided"]).union(set(self.distro[pp]["provides"]))): #direct and from-upward tags
                        s = self.up(pp, one_extra, depth, indent, version_req, verbose=verbose)
                        if s != '': r += [s]
                    return '\n'.join([i for i in r if i!= ''])   
        else:
            for one_pp in sorted(self.distro):
                s = self.up(one_pp, extra, depth, indent, version_req, verbose=verbose)
                if s != []: r += [s]
            if r !=[]:
                return '\n'.join([i for i in r if i!= ''])
            else:
                return

    def description(self, pp):
        "return description of the package"
        if pp in self.distro:
            return print("\n".join(self.distro[pp]["description"].split(r"\n")))
    
    def summary(self, pp):
        "return summary of the package"
        if pp in self.distro:
            return  self.distro[pp]["summary"]

    def pip_list(self, full=False, max_length=144):
        """do like pip list"""
        if full:
            return [(p, self.distro[p]["version"], sum_up(self.distro[p]["summary"]), max_length) for p in sorted(self.distro)]
        else:
            return [(p, sum_up(self.distro[p]["version"], max_length)) for p in sorted(self.distro)]

