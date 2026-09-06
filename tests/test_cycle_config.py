# -*- coding: utf-8 -*-
"""The cycle build workflow and the script that configures it must agree.

`.github/scripts/cycle_config.py` decides the whole shape of a cycle build,
and `build_winpython_cycle.yml` consumes that decision as `matrix.leg.<key>`
and `needs.config.outputs.<key>`. GitHub Actions resolves an expression naming
a key nothing emits to the empty string, silently: the build does not fail at
that line, it fails much later, in PowerShell, an hour into a Windows runner,
with an empty path. That is expensive to find and slow to retry, so this
module checks the two sides line up before any of it starts.

Nothing here needs pytest plugins, a YAML parser or a network: the workflow is
read as text and the script is imported and run for real, against whatever
cycle files the repository currently has. A new cycle is therefore covered the
moment its TOML is committed.
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CYCLES = REPO / "cycles"
SCRIPT = REPO / ".github/scripts/cycle_config.py"
WORKFLOW = REPO / ".github/workflows/build_winpython_cycle.yml"

cycle_files = sorted(CYCLES.glob("*.toml")) if CYCLES.is_dir() else []

needs_script = pytest.mark.skipif(not SCRIPT.is_file(), reason="cycle_config.py is gone")
needs_workflow = pytest.mark.skipif(
    not WORKFLOW.is_file(), reason="build_winpython_cycle.yml is gone"
)
needs_cycles = pytest.mark.skipif(not cycle_files, reason="no cycle files to check")


def load_script():
    spec = importlib.util.spec_from_file_location("cycle_config", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cycle_config():
    if not SCRIPT.is_file():
        pytest.skip("cycle_config.py is gone")
    return load_script()


@pytest.fixture
def at_repo_root(monkeypatch):
    """A cycle file names its lockfile directory relative to the checkout root.

    CI runs the script from there; pytest may be invoked from anywhere.
    """
    monkeypatch.chdir(REPO)


@pytest.fixture(scope="module")
def workflow_text():
    if not WORKFLOW.is_file():
        pytest.skip("build_winpython_cycle.yml is gone")
    return WORKFLOW.read_text(encoding="utf-8")


def config_for(cycle_config, cycle_file: Path, requested: str = "all") -> dict:
    import tomllib

    with cycle_file.open("rb") as fh:
        cfg = tomllib.load(fh)
    return cycle_config.build_config(cfg, requested, cycle_file.stem)


def legs_of(config: dict) -> list[dict]:
    return json.loads(config["matrix"])["leg"]


@needs_script
@needs_cycles
@pytest.mark.parametrize("cycle_file", cycle_files, ids=lambda p: p.stem)
class TestCycleFile:
    """Every committed cycle must still describe a build that could run."""

    def test_builds_at_least_one_leg(self, cycle_config, at_repo_root, cycle_file):
        """A cycle whose lockfiles are all missing would start runners for nothing.

        The script is meant to refuse that here, so an empty matrix means the
        cycle directory and the flavor names have drifted apart.
        """
        assert legs_of(config_for(cycle_config, cycle_file))

    def test_every_leg_names_a_lockfile_that_exists(self, cycle_config, at_repo_root, cycle_file):
        """The leg is what pip is pointed at; a stale name fails only on the runner."""
        for leg in legs_of(config_for(cycle_config, cycle_file)):
            assert Path(leg["lockfile"]).is_file(), f"{leg['winpyver']}: {leg['lockfile']}"
            for optional in ("lockfile_wheels", "requirements_wheels"):
                if leg[optional]:
                    assert Path(leg[optional]).is_file(), f"{leg['winpyver']}: {leg[optional]}"

    def test_artifact_names_are_unique(self, cycle_config, at_repo_root, cycle_file):
        """Two legs sharing an artifact name would race to upload the same one."""
        names = [leg["artifact_name"] for leg in legs_of(config_for(cycle_config, cycle_file))]
        assert len(names) == len(set(names)), sorted(names)

    def test_version_matches_the_tarball_it_downloads(self, cycle_config, cycle_file):
        """ver2 and src are hand-edited together; a copy-paste slip must not pass.

        The script raises on the mismatch, so reaching a leg at all is the check.
        """
        import tomllib

        with cycle_file.open("rb") as fh:
            cfg = tomllib.load(fh)
        for requested, entry in cfg["pythons"].items():
            facts = cycle_config.python_facts(requested, entry)
            assert ".".join(facts["ver2"].split(".")[:3]) in entry["src"]

    def test_free_threaded_pythons_build_only_free_threaded_flavors(
        self, cycle_config, at_repo_root, cycle_file
    ):
        """3.14 and 3.14F share a ver2, so only the flavor set separates them.

        If the WINPYARCHDET filter ever stopped applying, a free-threaded run
        would silently rebuild the ordinary flavors under the same file names.
        """
        for leg in legs_of(config_for(cycle_config, cycle_file)):
            free_threaded = leg["python_versionf"].endswith("F")
            assert leg["name"].endswith("f") == free_threaded, leg["winpyver"]


@needs_script
@needs_cycles
class TestDispatchChoices:
    @needs_workflow
    @pytest.mark.parametrize("cycle_file", cycle_files, ids=lambda p: p.stem)
    def test_every_python_can_be_dispatched_on_its_own(self, cycle_file, workflow_text):
        """The choice list is typed by hand; a cycle's new Python must be added to it.

        Without this, a cycle can offer 3.16 that "all" builds but that nobody
        can re-run alone when one flavor fails.
        """
        import tomllib

        with cycle_file.open("rb") as fh:
            pythons = set(tomllib.load(fh)["pythons"])
        block = re.search(r"\n        options:\n((?:\s+- '[^']+'\n)+)", workflow_text)
        assert block, "the python_versionf choice list moved; this test needs updating"
        offered = set(re.findall(r"- '([^']+)'", block.group(1)))
        assert "all" in offered
        assert pythons <= offered, f"{cycle_file.stem} offers {pythons - offered}, the workflow does not"


@needs_script
class TestReleaseTag:
    """The tag is what the download URLs the website publishes are built on."""

    @pytest.mark.parametrize("cycle,cfg,expected", [
        ("2026_04", {"release_level": "b1"}, "2026-04b1"),
        ("2026_03", {"release_level": ""}, "2026-03"),
        ("2026_04", {}, "2026-04"),
        ("2027_01", {"release_level": "rc2"}, "2027-01rc2"),
    ])
    def test_derived_from_the_cycle_name_and_level(self, cycle_config, cycle, cfg, expected):
        """A respin is a release_level bump, not a tag to invent.

        Deliberately no date in it: a date would tie the tag to a run, so
        re-running one missing flavor would open a second release instead of
        adding to the one the other legs are already on.
        """
        assert cycle_config.release_tag(cfg, cycle) == expected

    def test_an_explicit_tag_wins(self, cycle_config):
        """Kept for continuity with the tags releases used before this scheme."""
        cfg = {"release_level": "b1", "release_tag": "17.12.20260522/WinPython"}
        assert cycle_config.release_tag(cfg, "2026_04") == "17.12.20260522/WinPython"

    @pytest.mark.parametrize("bad", [
        "2026 04", "2026-04^b1", "2026~04", "cycle..04", "2026-04/", "2026-04.lock",
        "2026-04:b1", "back\\slash", "tab\there",
    ])
    def test_a_tag_git_would_refuse_is_caught_here(self, cycle_config, bad):
        """Five seconds into the config job beats an hour into a build."""
        with pytest.raises(SystemExit):
            cycle_config.release_tag({"release_tag": bad}, "2026_04")

    @needs_cycles
    @pytest.mark.parametrize("cycle_file", cycle_files, ids=lambda p: p.stem)
    def test_every_cycle_has_a_usable_tag(self, cycle_config, at_repo_root, cycle_file):
        tag = config_for(cycle_config, cycle_file)["release_tag"]
        assert tag and not set(tag) & cycle_config.TAG_FORBIDDEN


@needs_script
class TestReleaseTitle:
    """The title people actually read on the releases page.

    Reproduced from the titles written by hand for years rather than invented:
    cycle, then the level after a space -- the tag runs them together, the
    title does not -- then the date with no comma, which is how all but one of
    the previous titles read.
    """

    @pytest.mark.parametrize("cycle,level,date,expected", [
        # the real titles of these releases, to the letter
        ("2026_03", "", (2026, 8, 22), "WinPython 2026-03 of August 22nd 2026"),
        ("2026_03", "b3", (2026, 8, 8), "WinPython 2026-03 b3 of August 8th 2026"),
        ("2026_02", "b2", (2026, 5, 1), "WinPython 2026-02 b2 of May 1st 2026"),
        ("2026_01", "final", (2026, 3, 10), "WinPython 2026-01 final of March 10th 2026"),
        ("2025_05", "rc", (2025, 12, 22), "WinPython 2025-05 rc of December 22nd 2025"),
        ("2026_01", "b3", (2026, 2, 24), "WinPython 2026-01 b3 of February 24th 2026"),
    ])
    def test_matches_the_titles_used_before(self, cycle_config, cycle, level, date, expected):
        import datetime

        cfg = {"release_level": level} if level else {}
        assert cycle_config.release_title(cfg, cycle, datetime.date(*date)) == expected

    def test_no_double_space_when_there_is_no_level(self, cycle_config):
        """Some older titles read "2026-02  of May 17th": a level that was empty."""
        import datetime

        title = cycle_config.release_title({"release_level": ""}, "2026_04", datetime.date(2026, 5, 17))
        assert "  " not in title

    @pytest.mark.parametrize("day,expected", [
        (1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"),
        (11, "11th"), (12, "12th"), (13, "13th"),  # not 11st/12nd/13rd
        (21, "21st"), (22, "22nd"), (23, "23rd"), (30, "30th"), (31, "31st"),
    ])
    def test_ordinals(self, cycle_config, day, expected):
        assert cycle_config.ordinal(day) == expected

    @needs_cycles
    @pytest.mark.parametrize("cycle_file", cycle_files, ids=lambda p: p.stem)
    def test_every_cycle_produces_a_title(self, cycle_config, at_repo_root, cycle_file):
        title = config_for(cycle_config, cycle_file)["release_title"]
        assert title.startswith("WinPython ") and " of " in title
        assert "\n" not in title, "a GITHUB_OUTPUT value has to stay on one line"


@needs_script
@needs_workflow
@needs_cycles
class TestWorkflowMatchesConfig:
    """What the workflow reads, the script has to emit -- for every cycle."""

    @pytest.fixture(scope="class")
    def emitted(self, request):
        """Leg keys and config outputs common to every cycle file."""
        module = load_script()
        monkey = pytest.MonkeyPatch()
        monkey.chdir(REPO)
        try:
            leg_keys, output_keys, formats = None, None, set()
            for cycle_file in cycle_files:
                config = config_for(module, cycle_file)
                output_keys = set(config) if output_keys is None else output_keys & set(config)
                for leg in legs_of(config):
                    leg_keys = set(leg) if leg_keys is None else leg_keys & set(leg)
                    formats |= set(leg["formats"])
        finally:
            monkey.undo()
        return {"leg": leg_keys, "outputs": output_keys, "formats": formats}

    def test_every_matrix_key_the_workflow_reads_is_emitted(self, workflow_text, emitted):
        """An unknown matrix.leg.<key> resolves to "" and breaks far from here."""
        used = set(re.findall(r"matrix\.leg\.([A-Za-z_][A-Za-z0-9_]*)", workflow_text))
        used |= set(re.findall(r"matrix\.leg\['([^']+)'\]", workflow_text))
        assert used - {"formats"} <= emitted["leg"], used - {"formats"} - emitted["leg"]

    def test_every_archive_format_the_workflow_reads_is_emitted(self, workflow_text, emitted):
        used = set(re.findall(r"matrix\.leg\.formats\.([A-Za-z0-9_]+)", workflow_text))
        used |= set(re.findall(r"matrix\.leg\.formats\['([^']+)'\]", workflow_text))
        assert used, "the workflow stopped reading the archive formats"
        assert used <= emitted["formats"], used - emitted["formats"]

    def test_declared_job_outputs_come_from_the_script(self, workflow_text, emitted):
        """`outputs:` forwards steps.cfg.outputs.<key>; the script must write it."""
        declared = dict(re.findall(
            r"^      ([a-z0-9_]+): \$\{\{ steps\.cfg\.outputs\.([a-z0-9_]+) \}\}$",
            workflow_text, re.MULTILINE,
        ))
        assert declared, "the config job's outputs block moved; this test needs updating"
        assert set(declared.values()) <= emitted["outputs"], (
            set(declared.values()) - emitted["outputs"]
        )

    def test_every_output_the_workflow_reads_is_declared(self, workflow_text):
        declared = set(re.findall(
            r"^      ([a-z0-9_]+): \$\{\{ steps\.cfg\.outputs\.[a-z0-9_]+ \}\}$",
            workflow_text, re.MULTILINE,
        ))
        used = set(re.findall(r"needs\.config\.outputs\.([a-z0-9_]+)", workflow_text))
        assert used <= declared, used - declared

    def test_nothing_still_reads_the_pre_cycle_matrix(self, workflow_text):
        """`matrix.flavor` was the one-Python-per-dispatch shape; it emits nothing now."""
        assert "matrix.flavor" not in workflow_text

    def test_publishing_is_gated_both_ways(self, workflow_text):
        """The binaries go either to the release or to an artifact -- never neither.

        Both gates have to exist: if the negative one were dropped, a run with
        publish off would build gigabytes and upload none of it.
        """
        assert "if: ${{ inputs.publish }}" in workflow_text
        assert "if: ${{ !inputs.publish }}" in workflow_text

    def test_the_changelog_pr_is_whole_cycle_only(self, workflow_text):
        """A single-leg re-run would reduce the branch to that leg's files.

        It has nothing to add either way: the same lockfile builds the same
        package list, so a rebuilt leg cannot change a changelog.
        """
        assert "if: ${{ inputs.publish && inputs.python_versionf == 'all' }}" in workflow_text
        assert ".github/scripts/changelog_files.py release_metadata changelogs" in workflow_text
        assert (REPO / ".github/scripts/changelog_files.py").is_file()

    def test_the_release_title_is_built_by_the_script(self, workflow_text):
        """Ordinal dates are miserable in shell, and untestable there."""
        assert 'TITLE: ${{ needs.config.outputs.release_title }}' in workflow_text
        assert '--title "$TITLE"' in workflow_text

    def test_the_changelog_name_carries_the_release_level(self, workflow_text):
        """A beta and the final it becomes share a ver2.

        Without the level in the name, a b1's package list is written to the
        file the final release wants, and `changelogs/` briefly describes a
        beta under the final's name. The level has to reach the composite
        action for that, so both halves are checked.
        """
        assert "release_level: ${{ needs.config.outputs.release_level }}" in workflow_text
        action = (REPO / ".github/actions/publish-winpython/action.yml").read_text(encoding="utf-8")
        assert re.search(r"^  release_level:$", action, re.MULTILINE), "action input is missing"
        assert "${{ inputs.winpy_ver2 }}${{ inputs.release_level }}.md" in action

    def test_the_release_tag_is_never_taken_from_a_dispatch_input(self, workflow_text):
        """One source of truth: the cycle file. An input would let them disagree."""
        assert "inputs.release_tag" not in workflow_text
        for env_line in re.findall(r"^          TAG: (.+)$", workflow_text, re.MULTILINE):
            assert env_line == "${{ needs.config.outputs.release_tag }}", env_line
