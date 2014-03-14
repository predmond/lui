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
  def __init__(self):

    text = [
        ('title', "LUI"), "    ",
        ('key', "F1"), " Help ",
        ('key', "F3"), " Cycle-focus ",
        ('key', "F10"), " Quit "
        ]

    super(StatusWin, self).__init__(text)

    #self.keys = [#('F1', 'Help', curses.KEY_F1),
    #             ('F3', 'Cycle-focus', curses.KEY_F3),
    #             ('F10', 'Quit', curses.KEY_F10)]

  #def draw(self):
  #  self.win.addstr(0, 0, '')
  #  for key in self.keys:
  #    self.win.addstr('{0}'.format(key[0]), curses.A_REVERSE)
  #    self.win.addstr(' {0} '.format(key[1]), curses.A_NORMAL)
  #  super(StatusWin, self).draw()

  #def handleEvent(self, event):
  #  if isinstance(event, int):
  #    pass
  #  elif isinstance(event, lldb.SBEvent):
  #    if lldb.SBProcess.EventIsProcessEvent(event):
  #      state = lldb.SBProcess.GetStateFromEvent(event)
  #      status = lldbutil.state_type_to_str(state)
  #      self.win.erase()
  #      x = self.win.getmaxyx()[1] - len(status) - 1
  #      self.win.addstr(0, x, status)
  #  return

