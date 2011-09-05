#!/usr/bin/env python
"""
Convert a PyMake or filtered strace log file to a build system analysis JSON
format file.
"""

from argparse import ArgumentParser, FileType
from sys import exit, stdin, stdout, stderr

parser = ArgumentParser(description=__doc__)
parser.add_argument('input', metavar='FILE', type=FileType('r'), nargs='?', 
                    default=stdin,
                    help='PyMake or filtered strace log file to convert. The' \
                    ' default input file is stdin.')
parser.add_argument('-f', '--format', dest='format', default='strace',
                    help='The format of the given log files. Possible values' \
                    ' are ``strace`` and ``pymake``. By default, ``strace``' \
                    ' is used as input format.')
parser.add_argument('-o', '--output', dest='output', type=FileType('w'),
                    default=stdout,
                    help='The JSON format file will be written to' \
                    ' OUTPUT_FILE. The default output file is stdout.')
parser.add_argument('-t', '--threshold', type=float, default=0.1,
                    help='Minimal amount of elapsed time in seconds to' \
                    ' include a process and/or syscall in the output. The' \
                    ' default threshold is ``0.1`` seconds.')

args = parser.parse_args()

if args.format not in ['strace', 'pymake']:
    print >>stderr, \
            'Format "%s" is unknown. See -h for supported formats.' % \
            args.format
    exit(1)

getattr(__import__('backend.' + args.format), args.format).main(args)
