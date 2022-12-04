#!/usr/bin/env python
import sys
from winpython import associate, utils
from argparse import ArgumentParser

parser = ArgumentParser(description="unRegister Python file extensions, icons "\
                        "and Windows explorer context menu to a target "\
                        "Python distribution.")
try:
    str_type = unicode
except NameError:
    str_type = str
parser.add_argument('--target', metavar='path', type=str,
                    default=sys.prefix,
                    help='path to the target Python distribution')
parser.add_argument('--all', dest='all', action='store_const',
                    const=True, default=False,
                    help='unregister to all users, requiring administrative '\
                         'privileges (default: register to current user only)')
args = parser.parse_args()

print(args.target)
if utils.is_python_distribution(args.target):
    associate.unregister(args.target, current=not args.all)
else:
    raise WindowsError(f"Invalid Python distribution {args.target}")
