# -*- coding: utf-8 -*-
"""
hash.py: compute hash of given files into a markdown output
"""
# Copyright © 2014-2025+ The Winpython development team https://github.com/winpython/
# Licensed under the terms of the MIT License
# (see winpython/__init__.py for details)

from pathlib import Path
import sys
import hashlib

def compute_hash(file_path, hash_function, digest_size=None):
    """Compute the hash of a file using the specified hash function."""
    try:
        with open(file_path, 'rb') as file:
            if digest_size:
                return hash_function(file.read(), digest_size=digest_size).hexdigest()
            return hash_function(file.read()).hexdigest()
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def print_hashes(files):
    """Print the hashes of the given files."""
    header = f"{'MD5':<32} | {'SHA-1':<40} | {'SHA-256':<64} | {'Binary':<33} | {'Size':<20} | {'blake2b-256':<64}"
    line = "|".join(["-" * len(part) for part in header.split("|")])

    print(header)
    print(line)

    for file in sorted(files):
        md5 = compute_hash(file, hashlib.md5)
        sha1 = compute_hash(file, hashlib.sha1)
        sha256 = compute_hash(file, hashlib.sha256)
        name = Path(file).name.ljust(33)
        size = f"{Path(file).stat().st_size:,} Bytes".replace(",", " ").rjust(20)
        blake2b = compute_hash(file, hashlib.blake2b, digest_size=32)
        print(f"{md5} | {sha1} | {sha256} | {name} | {size} | {blake2b}")
        
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: hash.py files_to_compute_hash")
        sys.exit(1)
    files = [file for file in sys.argv[1:] if file[-3:].lower() != ".py"]
    print_hashes(files)
