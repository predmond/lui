##===-- eventwin.py ------------------------------------------*- Python -*-===##
##
##                     The LLVM Compiler Infrastructure
##
## This file is distributed under the University of Illinois Open Source
## License. See LICENSE.TXT for details.
##
##===----------------------------------------------------------------------===##

import urwid
import lldb, lldbutil

class EventWalker(urwid.ListWalker):
  def __init__(self):
    self.events = []
    self.focus = 0

  def add(self, event):
    text = urwid.Text(lldbutil.get_description(event))
    self.events.append(text)
    self.set_focus(len(self.events)-1)
    return

  def get_focus(self):
    return self._get_at_pos(self.focus)

  def set_focus(self, focus):
    self.focus = focus
    self._modified()

  def get_next(self, start_from):
    return self._get_at_pos(start_from + 1)

  def get_prev(self, start_from):
    return self._get_at_pos(start_from - 1)

  def _get_at_pos(self, pos):
   if pos < 0:
     return None, None
   if len(self.events) > pos:
     return self.events[pos], pos
   else:
     return None, None

class EventWin(urwid.ListBox):
  def __init__(self, event_queue):
    self.walker = EventWalker()
    super(EventWin, self).__init__(self.walker)
    event_queue.add_listener(self)

  def handle_lldb_event(self, event):
    self.walker.add(event)
    return

