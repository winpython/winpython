"""File a cycle's build output into changelogs/.

    python .github/scripts/changelog_files.py <downloaded metadata> changelogs

A build leg produces four metadata files. Three of them belong in changelogs/
and are copied there as they are: the package index
(WinPython<flavor>-64bit-<version>.md), the lock file and the requirements.
The fourth, hashes_<winpyver>.md, describes the binaries of one build rather
than the release, and stays out.

No _History.md companion is written. A history compares a release against the
one immediately before it, and that chain carries no meaning: flavors are not
stable across cycles -- one may appear while another goes away -- and people
upgrade about once a year rather than every cycle, so a diff against the
predecessor answers a question almost nobody asks. What is useful is comparing
two package indexes of the reader's own choosing, which `wppm -diff` does
against any two of the files this script files.

"""
import re
import shutil
import sys
from pathlib import Path

# Running a script puts the script's own directory on sys.path, not the
# checkout root, so wppm has to be found deliberately: this file is
# .github/scripts/changelog_files.py, hence two levels up. Without it the
# import finds whatever wppm happens to be installed, or -- as on a CI runner,
# which installs none -- nothing at all.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from wppm.diff import version  # noqa: E402  packaging, or pip's vendored copy

# WinPythonslim-64bit-3.15.0.5b1.md -- the flavor may be empty, and the version
# may carry a release level, which is why the parser decides and not the regex
CHANGELOG = re.compile(r"^WinPython(?P<flavor>[A-Za-z0-9]*)-(?P<arch>\d+)bit-(?P<version>.+)\.md$")


def parse_changelog_name(name: str):
    """(flavor, architecture, version) for a package index, else None."""
    match = CHANGELOG.match(name)
    if not match:
        return None
    try:
        version.parse(match.group("version"))
    except version.InvalidVersion:
        return None  # anything whose tail is not a version is not an index
    return match.group("flavor"), int(match.group("arch")), match.group("version")


def files_to_file(source: Path):
    """The build output that belongs in changelogs/.

    The package index, the lock file and the requirements -- and so not
    hashes_<winpyver>.md, which describes one build's binaries rather than the
    release. It is excluded by being neither: it is not named for a version,
    and it is not a pylock or a requir.
    """
    for path in sorted(source.iterdir()):
        if not path.is_file():
            continue
        if parse_changelog_name(path.name) or path.name.startswith(("pylock.", "requir.")):
            yield path


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        raise SystemExit(f"usage: {Path(argv[0]).name} <metadata dir> <changelogs dir>")
    source, changelogs = Path(argv[1]), Path(argv[2])
    if not source.is_dir():
        raise SystemExit(f"no such directory: {source}")
    if not changelogs.is_dir():
        raise SystemExit(f"no such directory: {changelogs}")

    filed = []
    for path in files_to_file(source):
        shutil.copyfile(path, changelogs / path.name)
        filed.append(path.name)
    if not filed:
        raise SystemExit(f"{source} held no changelog, lock file or requirements")
    for name in filed:
        print(f"filed {name}")
    indexes = sum(1 for name in filed if parse_changelog_name(name))
    print(f"\n{len(filed)} file(s) filed, {indexes} package index(es)")


if __name__ == "__main__":
    main(sys.argv)
