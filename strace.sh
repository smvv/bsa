#!/bin/sh

#syscalls="exit_group|vfork|execve|wait4"
#syscalls="$syscalls|<\.\.\. ($syscalls)"
#
#echo "Starting strace and grep for $syscalls."
#
# Redirect only stderr to a pipe.
#exec 3>&1
#strace -ftts 1024 -e trace=process make -sj12 $@ 2>&1 >&3 3>&- | \
#    egrep "^(\[pid +[0-9]+\] )?[0-9:.]{15} ($syscalls)|^(\)|Process)" \
#    3>&- > strace.log
#exec 3>&-
strace -ftts 1024 -e trace=process make -sj12 $@ &> strace.log
