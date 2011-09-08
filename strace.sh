#!/bin/sh
strace -qftts 1024 -e trace=process -o strace.log make -sj12 $@
