Build system analysis for PyMake and Make
=========================================

Build system analysis allows developers to construct a build order diagram from
a (Py)Make build system. 

Usage instructions for Make
---------------------------

For Make, strace is used to get all required information (start time, end time,
arguments) about the invoked sub processes. A filtered strace log file of Make
is required to construct the build order diagram:

  syscalls="exit_group|vfork|execve|wait4"
  syscalls="$syscalls|<\.\.\. ($syscalls)"
  strace -ftts 1024 make -Bsj12 2>&1 | \
      egrep "^(\[pid +[0-9]+\] )?[0-9:.]{15} ($syscalls)|^(\)|Process)" \
      > strace.log

  ./convert.py --format=strace -o static/data/bsa.json strace.log

Usage instructions for PyMake
-----------------------------

For PyMake, use the ``--print-bsa`` flag to output the required information:

  pymake -Bsj12 --print-bsa > static/data/bsa.json
