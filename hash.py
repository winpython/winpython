# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 21:30:06 2015

@author: famille
"""

import io
import os
import sys
import hashlib


def give_hash(file_in, with_this):
    with io.open(file_in, 'rb') as f:
        return with_this(f.read()).hexdigest()

def give_hashblake(file_in, with_this):
    with io.open(file_in, 'rb') as f:
        return with_this(f.read(),digest_size=32).hexdigest()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(
            "Usage: "
            + sys.argv[0]
            + " github-user [github-project]"
        )
        exit(1)
    file = sys.argv[1]

    header = (
        " MD5"
        + " " * (32 - 4)
        + " | SHA-1"
        + " " * (40 - 5)
        + " | SHA-256"
        + " " * (64 - 7)
        + " | Binary"
        + " " * (33 - 5)
        + "| Size"
        + " " * (20 - 6)
        #+ " | SHA3-256"
        #+ " " * (64 - 8)
        + " | blake2b-256"
        + " " * (64 - 11)
   )
    line = "|".join(
        ["-" * len(i) for i in header.split("|")]
    )

    print(header)
    print(line)

    print(""+
        f"{give_hash(file, hashlib.md5)} | " +
        f"{give_hash(file, hashlib.sha1)} | " +
        f"{give_hash(file, hashlib.sha256)} | " +
        f"{os.path.basename(file):33} |"+
		f"{os.path.getsize(file):13,}".replace(",", " ") +  ' Bytes | '   +
        # f" | {give_hash(file, hashlib.sha3_256)}"
        f"{give_hashblake(file, hashlib.blake2b)}")
        
         

