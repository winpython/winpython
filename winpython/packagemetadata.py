# -*- coding: utf-8 -*-
"""
packagemetadata.py - get metadata from designated place
"""
import os
import re
import tarfile
import zipfile
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from . import utils
import importlib.metadata
import email
from packaging.utils import canonicalize_name
# --- Abstract metadata accessor ---

class PackageMetadata:
    """A minimal abstraction for package metadata."""
    def __init__(self, name, version, requires, summary, description, metadata):
        self.name = name
        self.version = version
        self.requires = requires  # List[str] of dependencies
        self.summary = summary
        self.description = description
        self.metadata = metadata

def get_installed_metadata(path = None) -> List[PackageMetadata]:
    # Use importlib.metadata or pkg_resources
    pkgs = []
    distro = importlib.metadata.distributions(path = path) if path else importlib.metadata.distributions()
    for dist in distro:
        name = canonicalize_name(dist.metadata['Name'])
        version = dist.version
        summary = dist.metadata.get("Summary", ""),
        description = dist.metadata.get("Description", ""),
        requires = dist.requires or []
        metadata = dist.metadata
        pkgs.append(PackageMetadata(name, version, requires, summary, description, metadata))
    return pkgs

def get_directory_metadata(directory: str) -> List[PackageMetadata]:
    # For each .whl/.tar.gz file in directory, extract metadata
    pkgs = []
    for fname in os.listdir(directory):
        if fname.endswith('.whl'):
            # Extract METADATA from wheel
            meta = extract_metadata_from_wheel(os.path.join(directory, fname))
            pkgs.append(meta)
        elif fname.endswith('.tar.gz'):
            # Extract PKG-INFO from sdist
            meta = extract_metadata_from_sdist(os.path.join(directory, fname))
            pkgs.append(meta)
    return pkgs

def extract_metadata_from_wheel(path: str) -> PackageMetadata:
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if name.endswith(r'.dist-info/METADATA') and name.split("/")[1] == "METADATA":
                with zf.open(name) as f:
                    # Parse metadata (simple parsing for Name, Version, Requires-Dist)
                    return parse_metadata_file(f.read().decode())
        raise ValueError(f"No METADATA found in {path}")

def extract_metadata_from_sdist(path: str) -> PackageMetadata:
    with tarfile.open(path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith('PKG-INFO'):
                f = tf.extractfile(member)
                return parse_metadata_file(f.read().decode())
    raise ValueError(f"No PKG-INFO found in {path}")

def parse_metadata_file(txt: str) -> PackageMetadata:
    meta = email.message_from_string(txt)
    name = canonicalize_name(meta.get('Name', ''))
    version = meta.get('Version', '')
    summary = meta.get('Summary', '')
    description = meta.get('Description', '')
    requires = meta.get_all('Requires-Dist') or []
    return PackageMetadata(name, version, requires, summary, description, dict(meta.items()))

def main():
    if len(sys.argv) > 1:
        # Directory mode
        directory = sys.argv[1]
        pkgs = get_directory_metadata(directory)
    else:
        # Installed packages mode
        pkgs = get_installed_metadata()

if __name__ == "__main__":
    main()