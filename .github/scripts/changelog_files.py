"""File a cycle's build output into changelogs/, and write the histories.

    python .github/scripts/changelog_files.py <downloaded metadata> changelogs

A build leg produces four metadata files. Three of them belong in changelogs/
and are copied there as they are: the package index
(WinPython<flavor>-64bit-<version>.md), the lock file and the requirements.
The fourth, hashes_<winpyver>.md, describes the binaries of one build rather
than the release, and stays out.

The _History.md companions are then written here rather than shipped from the
build, because a history is a comparison against the *previous* release, and
only a checkout of the repository has that to compare against. Ordering is
`wppm.diff`'s job; this decides what to hand it.

Run from the checkout root, so `from wppm import diff` finds the wppm being
released rather than an installed one.
"""
import re
import shutil
import sys
from pathlib import Path

from wppm import diff
from wppm.diff import version  # packaging, or pip's vendored copy

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
        return None  # the _History companions land here, as they should
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

    # every package index has to be in place before any history is written: a
    # history reads the index of the release it compares against, which for the
    # second flavor of a cycle may well be the one just copied
    histories = 0
    for name in filed:
        parsed = parse_changelog_name(name)
        if not parsed:
            continue
        flavor, architecture, ver = parsed
        previous = diff.find_previous_version(ver, changelogs, flavor, architecture)
        diff.write_changelog(ver, None, changelogs, flavor, architecture)
        histories += 1
        against = "nothing earlier" if previous == ver else previous
        print(f"history WinPython{flavor}-{architecture}bit-{ver} vs {against}")
    print(f"\n{len(filed)} file(s) filed, {histories} history file(s) written")


if __name__ == "__main__":
    main(sys.argv)
