"""Ensure that current version is not in conflict with published releases."""
from pkg_resources import parse_version
import subprocess as subp
from pathlib import PurePath
import urllib.request
import json
import warnings
import sys

project_dir = PurePath(__file__).parent.parent
version_fn = project_dir / "src/iminuit/version.py"
changelog_fn = project_dir / "doc/changelog.rst"

with open(version_fn) as f:
    version = {}
    exec(f.read(), version)
    with warnings.catch_warnings(record=True) as record:
        iminuit_version = parse_version(version["version"])
    if record:
        raise ValueError(record[0].message)
    documented_root = version["root_version"]

print("iminuit version:", iminuit_version)
print("root    version:", documented_root)

# check that root version is up-to-date
actual_root = (
    subp.check_output([sys.executable, project_dir / ".ci" / "root_version.py"])
    .decode()
    .strip()
)

assert (
    documented_root == actual_root
), f"ROOT version mismatch: {documented_root} != {actual_root}"

# make sure that changelog was updated
with open(changelog_fn) as f:
    assert str(iminuit_version) in f.read(), "changelog entry missing"

# make sure that version is not already tagged
tags = subp.check_output(["git", "tag"]).decode().strip().split("\n")
assert f"v{iminuit_version}" not in tags, "tag exists"

# make sure that version itself was updated
with urllib.request.urlopen("https://pypi.org/pypi/iminuit/json") as r:
    pypi_versions = [parse_version(v) for v in json.loads(r.read())["releases"]]

pypi_versions.sort()
print("PyPI    version:", pypi_versions[-1])

assert iminuit_version not in pypi_versions, "pypi version exists"
