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


if __name__ == '__main__':
 if (len(sys.argv) < 2):
    print ("Usage: " + sys.argv[0] + " github-user [github-project]")
    exit(1)
 file = sys.argv[1]
        
 header = (" MD5"+" "*(32-4)+" | SHA-1"+" "*(40-5)+" | SHA-256"+
          " "*(64-7)+" | Binary"+" "*(31-5)+"| Size"+" "*(20-6))
 line = "|".join(["-"*len(i) for i in header.split("|")])

 print(header)
 print(line)
 print ("%s | %s | %s | %s | %s" % (give_hash(file, hashlib.md5),
        give_hash(file, hashlib.sha1),
        give_hash(file, hashlib.sha256),
        '{0:31s}'.format(os.path.basename(file)),
        ('{0:12,}'.format(os.path.getsize(file)).replace(","," ")+ ' Bytes')
        ))
