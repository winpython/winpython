# -*- coding: utf-8 -*-
"""Dependency-tree reading, against a synthetic site-packages.

Hand-written .dist-info gives full control of the graph -- extras, missing
packages, cycles -- without installing anything.
"""
import pytest

from wppm import piptree

from conftest import write_dist


@pytest.fixture
def graph(tmp_path):
    """A small dependency graph:

        app 1.0 -> lib >=1.0 -> helper
        app[extra] -> optional (not installed)
        orphan 9.9 (nothing depends on it)
    """
    root = tmp_path / "dist"
    site = root / "Lib" / "site-packages"
    site.mkdir(parents=True)
    (root / "python.exe").write_bytes(b"MZ")
    write_dist(site, "app", "1.0", summary="The application",
               requires=["lib>=1.0", 'optional>=2.0; extra == "fancy"'],
               extras=["fancy"])
    write_dist(site, "lib", "1.5", summary="A library", requires=["helper"])
    write_dist(site, "helper", "0.3", summary="A helper")
    write_dist(site, "orphan", "9.9", summary="Depends on nothing")
    return root


@pytest.fixture
def pip(graph):
    return piptree.PipData(str(graph))


class TestPipList:
    def test_lists_every_installed_package(self, pip):
        assert {n for n, _, _ in pip.pip_list(full=True)} == {
            "app", "lib", "helper", "orphan"
        }

    def test_reports_version_and_summary(self, pip):
        rows = {n: (v, s) for n, v, s in pip.pip_list(full=True)}
        assert rows["app"] == ("1.0", "The application")

    def test_reads_from_the_target_not_the_running_interpreter(self, pip):
        """wppm itself must not leak into a -t listing."""
        assert "pytest" not in {n for n, _, _ in pip.pip_list(full=True)}


class TestDown:
    def test_shows_direct_dependency(self, pip):
        out = pip.down("app", "", 1)
        assert "app==1.0" in out
        assert "lib==1.5" in out

    def test_recurses_to_the_requested_depth(self, pip):
        assert "helper==0.3" in pip.down("app", "", 2)
        assert "helper==0.3" not in pip.down("app", "", 1)

    def test_leaf_package_has_no_dependencies(self, pip):
        out = pip.down("helper", "", 2)
        assert "helper==0.3" in out
        assert "lib==" not in out

    def test_extra_pulls_in_optional_dependency(self, pip):
        out = pip.down("app", "fancy", 1)
        assert "optional" in out

    def test_uninstalled_dependency_is_marked_unknown(self, pip):
        """`optional` is required by an extra but not installed."""
        assert "optional==?" in pip.down("app", "fancy", 1)

    def test_json_output_parses(self, pip):
        import json
        parsed = json.loads(pip.down("app", "", 2, format="json"))
        assert parsed


class TestUp:
    def test_finds_reverse_dependency(self, pip):
        out = pip.up("helper", "", 1)
        assert "helper==0.3" in out
        assert "lib==1.5" in out

    def test_recurses_upward(self, pip):
        assert "app==1.5" not in pip.up("helper", "", 2)
        assert "app==1.0" in pip.up("helper", "", 2)

    def test_orphan_has_no_dependants(self, pip):
        out = pip.up("orphan", "", 2)
        assert "orphan==9.9" in out
        assert "app==" not in out


class TestMarkerEnvironment:
    """Characterisation tests: markers are evaluated against the RUNNING
    interpreter, not the -t target. That is a known limitation -- see
    piptree._get_environment. If someone fixes it, these tests should fail
    and be rewritten deliberately rather than silently drift.
    """

    def test_environment_describes_the_running_interpreter(self, pip):
        import platform
        assert pip.environment["python_version"] == ".".join(
            platform.python_version_tuple()[:2]
        )

    def test_environment_exposes_every_marker_field_packaging_needs(self, pip):
        assert set(pip.environment) >= {
            "implementation_name", "os_name", "platform_machine",
            "platform_system", "python_full_version", "python_version",
            "sys_platform",
        }


class TestWheelhouse:
    """Reading a directory of wheels instead of an installation."""

    @pytest.fixture
    def wheelhouse(self, tmp_path):
        import zipfile
        house = tmp_path / "wheels"
        house.mkdir()

        def wheel(name, version, requires=()):
            with zipfile.ZipFile(house / f"{name}-{version}-py3-none-any.whl", "w") as zf:
                lines = ["Metadata-Version: 2.1", f"Name: {name}", f"Version: {version}"]
                lines += [f"Requires-Dist: {r}" for r in requires]
                zf.writestr(f"{name}-{version}.dist-info/METADATA", "\n".join(lines) + "\n")

        wheel("solo", "1.0")
        wheel("twice", "1.0", requires=["solo"])
        wheel("twice", "2.0")
        (house / "not-a-package.tar.gz").write_bytes(b"not a tarball at all")
        return house

    def test_an_unreadable_archive_does_not_lose_the_others(self, wheelhouse):
        pip = piptree.PipData(None, str(wheelhouse))
        assert {"solo", "twice"} <= set(pip.distro)

    def test_only_the_newest_version_of_a_package_is_kept(self, wheelhouse):
        pip = piptree.PipData(None, str(wheelhouse))
        assert pip.distro["twice"]["version"] == "2.0"

    def test_the_newest_version_brings_its_own_dependencies(self, wheelhouse):
        """twice 1.0 needs solo, twice 2.0 does not: the answer must be 2.0's."""
        pip = piptree.PipData(None, str(wheelhouse))
        assert pip.dependency_closure("twice") == set()


class TestCycles:
    def test_mutual_dependency_terminates(self, tmp_path):
        """A <-> B must not recurse forever."""
        root = tmp_path / "cyc"
        site = root / "Lib" / "site-packages"
        site.mkdir(parents=True)
        write_dist(site, "aaa", "1.0", requires=["bbb"])
        write_dist(site, "bbb", "1.0", requires=["aaa"])
        pip = piptree.PipData(str(root))
        assert "aaa==1.0" in pip.down("aaa", "", 10)
        assert "bbb==1.0" in pip.up("bbb", "", 10)
