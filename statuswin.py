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

class StatusWin(urwid.Columns):
  def __init__(self, event_queue):
    event_queue.add_listener(self)

    items = [
        ('title', "LUI"), "    ",
        ('key', "F1"), " Help ",
        ('key', "F3"), " Cycle-focus ",
        ('key', "F10"), " Quit "
      ]
    self.text = urwid.Text(items)
    self.status = urwid.Text('', align='right')
    self.status_attr = urwid.AttrWrap(self.status, 'stopped')
    super(StatusWin, self).__init__([self.text, self.status_attr])

  def handle_lldb_event(self, event):
    if lldb.SBProcess.EventIsProcessEvent(event):
      state = lldb.SBProcess.GetStateFromEvent(event)
      status = lldbutil.state_type_to_str(state)
      if status == 'running':
        self.status_attr.set_attr('running')
      elif status == 'stopped':
        self.status_attr.set_attr('stopped')
      elif status == 'exited':
        self.status_attr.set_attr('exited')
      else:
        self.status_attr.set_attr(None)
      self.status.set_text('%s' % status)
