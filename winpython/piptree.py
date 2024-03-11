# -*- coding: utf-8 -*-
import json, sys, re, platform, os, sysconfig
import re
from winpython import utils
from collections import OrderedDict
from pip._vendor.packaging.markers import Marker


def normalize(this):
    """apply https://peps.python.org/pep-0503/#normalized-names"""
    return re.sub(r"[-_.]+", "-", this).lower()


class pipdata:
    """Wrapper aroud pip inspect"""

    def __init__(self, Target=None):

        # get pip_inpsect raw data in json form
        #os.environ["pythonutf8"] = "1" causes issues in movable, so limit to there
        if Target == None:
            #pip_inspect = utils.exec_run_cmd(["pip", "inspect"])
            pip_inspect = utils.exec_shell_cmd(f'set pythonutf8=1 & python -X utf8=1 -m pip inspect', sys.prefix)        
        else:
            #pip_inspect = utils.exec_run_cmd([Target , "-X" ,"utf8=1", "-m", "pip", "inspect"]) 
            pip_inspect = utils.exec_shell_cmd(f'set pythonutf8=1 & "{Target}" -X utf8=1 -m pip inspect', sys.prefix)          
        pip_json = json.loads(pip_inspect)

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
        replacements = str.maketrans({" ": "", "[": "", "]": "", "'": "", '"': ""})
        self.environment = {
            "implementation_name": sys.implementation.name,
            "implementation_version": "{0.major}.{0.minor}.{0.micro}".format(
                sys.implementation.version
            ),
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

        for p in pip_json["installed"]:
            meta = p["metadata"]
            name = meta["name"]
            key = normalize(name)
            requires = []
            self.raw[key] = meta
            if "requires_dist" in meta:
                for i in meta["requires_dist"]:
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
                "version": meta["version"],
                "summary": meta["summary"] if "summary" in meta else "",
                "requires_dist": requires,
                "wanted_per": [],
                "description": meta["description"] if "description" in meta else "",
            }
        # On a second pass, complement distro in reverse mode with 'wanted-per':
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
                    }  # req_key_extra
                    if "req_marker" in r:
                        want_add["req_marker"] = r["req_marker"]  # req_key_extra
                    self.distro[r["req_key"]]["wanted_per"] += [want_add]

    def _downraw(self, pp, extra="", version_req="", depth=20, path=[], verbose=False):
        """build a nested list of needed packages with given extra and depth"""
        envi = {"extra": extra, **self.environment}
        p = normalize(pp)

        # several extras request management: example dask[array,diagnostics] 
        extras = extra.split(",")

        ret_all = []
        if p+"["+extra+"]" in path: # for dask[complete]->dask[array,test,..]
            print("cycle!", "->".join(path + [p]))
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
        """build a nested list of user packages with given extra and depth"""
        envi = {"extra": extra, **self.environment}
        p = normalize(pp)
        ret_all = []
        if p in path:
            print("cycle!", "->".join(path + [p]))
        elif p in self.distro and len(path) <= depth:
            summary = f'  {self.distro[p]["summary"]}' if verbose else ''
            if extra == "":
                ret_all = [f'{p}=={self.distro[p]["version"]} {version_req}{summary}']
            else:
                ret_all = [f'{p}[{extra}]=={self.distro[p]["version"]} {version_req}{summary}']
            ret = []
            for r in self.distro[p]["wanted_per"]:
                if r["req_key"] in self.distro and r["req_key"] not in path:
                    if "req_marker" not in r or Marker(r["req_marker"]).evaluate(
                        environment=envi
                    ):
                        ret += self._upraw(
                            r["req_key"],
                            "",
                            f"[requires: {p}"
                            + (
                                "[" + r["req_extra"] + "]"
                                if r["req_extra"] != ""
                                else ""
                            )
                            + f'{r["req_version"]}]',
                            depth,
                            path + [p],
                            verbose=verbose,
                        )
            if not ret == []:
                ret_all += [ret]
        return ret_all

    def down(self, pp="", extra="", depth=99, indent=5, version_req="", verbose=False):
        """print the downward requirements for the package or all packages"""
        if not pp == "":
            rawtext = json.dumps(
                self._downraw(pp, extra, version_req, depth, verbose=verbose), indent=indent
            )
            lines = [l for l in rawtext.split("\n") if len(l.strip()) > 2]
            print("\n".join(lines).replace('"', ""))
        else:
            for one_pp in sorted(self.distro):
                self.down(one_pp, extra, depth, indent, version_req, verbose=verbose)

    def up(self, pp, extra="", depth=99, indent=5, version_req="", verbose=False):
        """print the upward needs for the package"""
        rawtext = json.dumps(self._upraw(pp, extra, version_req, depth, verbose=verbose), indent=indent)
        lines = [l for l in rawtext.split("\n") if len(l.strip()) > 2]
        print("\n".join(lines).replace('"', ""))

    def description(self, pp):
        "return description of the package"
        if pp in self.distro:
            return print("\n".join(self.distro[pp]["description"].split(r"\n")))
    
    def summary(self, pp):
        "return summary of the package"
        if pp in self.distro:
            return  self.distro[pp]["summary"]

    def pip_list(self, full=False):
        """do like pip list"""
        if full:
            return [(p, self.distro[p]["version"], self.distro[p]["summary"]) for p in sorted(self.distro)]
        else:
            return [(p, self.distro[p]["version"]) for p in sorted(self.distro)]

