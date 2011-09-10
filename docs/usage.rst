Build system analysis for PyMake and Make
=========================================

Build system analysis allows developers to construct a build order diagram from
a (Py)Make build system. 

Usage instructions for Make
---------------------------

For Make, strace is used to get all required information (start time, end time,
arguments) about the invoked sub processes. A filtered strace log file of Make
is required to construct the build order diagram:

.. code-block:: console

  # In build directory, containing the root Makefile:
  $ /path/to/bsa/strace.sh
  $ /path/to/bsa/convert.py -o /path/to/bsa/static/data/bsa.json strace.log
  $ /path/to/bsa/viewer.py 1122

Start a web browser and go to http://localhost:1122 to view the analysis.

Usage instructions for PyMake
-----------------------------

For PyMake, use the ``--print-bsa`` flag to output the required information:

.. code-block:: console

  # In build directory, containing the root Makefile:
  $ pymake -Bsj12 --print-bsa > /path/to/bsa/static/data/bsa.json
  $ /path/to/bsa/viewer.py 1122

Note: pymake's support for bsa is work-in-progress and it's output file is at
the moment not compatible with bsa's viewer.
