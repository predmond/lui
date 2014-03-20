##===-- statuswin.py -----------------------------------------*- Python -*-===##
##
##                     The LLVM Compiler Infrastructure
##
## This file is distributed under the University of Illinois Open Source
## License. See LICENSE.TXT for details.
##
##===----------------------------------------------------------------------===##

import lldb, lldbutil
import urwid

class StatusWin(urwid.Text):
  def __init__(self, event_queue):
    event_queue.add_listener(self)

    self.items = [
        ('title', "LUI"), "    ",
        ('key', "F1"), " Help ",
        ('key', "F3"), " Cycle-focus ",
        ('key', "F10"), " Quit "
      ]
    super(StatusWin, self).__init__(self.items)

  def handle_lldb_event(self, event):
    if lldb.SBProcess.EventIsProcessEvent(event):
      state = lldb.SBProcess.GetStateFromEvent(event)
      status = lldbutil.state_type_to_str(state)
      self.set_text(self.items + [status])
