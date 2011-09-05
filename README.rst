Build system analysis for PyMake and Make
=========================================

Build system analysis allows developers to construct a build order diagram from
a (Py)Make build system. 

Usage instructions for Make
---------------------------

For Make, strace is used to get all required information (start time, end time,
arguments) about the invoked sub processes. A filtered strace log file of Make
is required to construct the build order diagram:

  strace -ftts 1024 -e trace=process make -sj12 $@ &> strace.log
  ./convert.py --format=strace -o static/data/bsa.json strace.log

Usage instructions for PyMake
-----------------------------

For PyMake, use the ``--print-bsa`` flag to output the required information:

  pymake -Bsj12 --print-bsa > static/data/bsa.json
