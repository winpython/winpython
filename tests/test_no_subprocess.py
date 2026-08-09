# -*- coding: utf-8 -*-
"""piptree must never spawn a process.

It runs inside JupyterLite/Pyodide, where process spawning does not exist.
This is the executable form of the rule stated in piptree's module docstring:
if someone makes PipData shell out to the target interpreter, these fail.
"""
import subprocess

import pytest

from wppm import piptree

from conftest import write_dist


class Spawned(Exception):
    """Raised instead of starting a process."""


@pytest.fixture
def no_spawn(monkeypatch):
    def boom(*args, **kwargs):
        raise Spawned("piptree must not spawn a process (it runs in Pyodide)")

    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, boom)
    return boom


@pytest.fixture
def target(tmp_path):
    root = tmp_path / "dist"
    site = root / "Lib" / "site-packages"
    site.mkdir(parents=True)
    (root / "python.exe").write_bytes(b"MZ")
    write_dist(site, "app", "1.0", summary="An app", requires=["lib"])
    write_dist(site, "lib", "2.0", summary="A lib")
    return root


def test_building_pipdata_spawns_nothing(no_spawn, target):
    assert piptree.PipData(str(target)).distro


def test_pip_list_spawns_nothing(no_spawn, target):
    pip = piptree.PipData(str(target))
    assert len(pip.pip_list(full=True)) == 2


def test_dependency_trees_spawn_nothing(no_spawn, target):
    pip = piptree.PipData(str(target))
    assert "lib==2.0" in pip.down("app", "", 2)
    assert "app==1.0" in pip.up("lib", "", 2)


def test_the_guard_itself_works(no_spawn):
    """Guard against a false negative: prove the patch really blocks spawning."""
    with pytest.raises(Spawned):
        subprocess.Popen(["cmd", "/c", "echo", "hi"])
