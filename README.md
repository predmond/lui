lui
===

LLDB (Terminal) User Interface
------------------------------

This directory contains the curses user interface for LLDB. To use it, ensure Python can find your lldb module. You may have to modify PYTHONPATH for that purpose:

$ export PYTHONPATH=/path/to/lldb/module

Then, run the lui.py. To load a core file:
$ ./lui.py --core core

To create a target from an executable:
$ ./lui.py /bin/echo "hello world"

To attach to a running process:
$ ./lui.py --attach <pid>


Known Issues
------------
1. Missing paging in command-window
2. Only minimal testing (on Ubuntu Linux x86_64)

Missing Features
----------------
- stdin/stdout/stderr windows
- memory window
- backtrace window
- threads window
- tab-completion
- syntax-highlighting (via pygments library)
- (local) variables window
- registers window
- disassembly window
- custom layout
