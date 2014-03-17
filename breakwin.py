##===-- breakwin.py ------------------------------------------*- Python -*-===##
##
##                     The LLVM Compiler Infrastructure
##
## This file is distributed under the University of Illinois Open Source
## License. See LICENSE.TXT for details.
##
##===----------------------------------------------------------------------===##

import urwid
import lldb, lldbutil
import re

class BreakWalker(urwid.ListWalker):
  def __init__(self, driver):
    self.breaks = []
    self.focus = 0
    self.driver = driver

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
   if len(self.breaks) > pos:
     return self.breaks[pos], pos
   else:
     return None, None

  def update(self):
    self.breaks = []

    target = self.driver.getTarget()
    if not target.IsValid():
      return

    #selected = self.getSelected()
    #self.clearItems()

    for i in range(0, target.GetNumBreakpoints()):
      bp = target.GetBreakpointAtIndex(i)
      if bp.IsInternal():
        continue
      text = lldbutil.get_description(bp)
      # FIXME: Use an API for this, not parsing the description.
      match = re.search('SBBreakpoint: id = ([^,]+), (.*)', text)
      try:
        id = match.group(1)
        desc = match.group(2).strip()
        if bp.IsEnabled():
          text = '%s: %s' % (id, desc)
        else:
          text = '%s: (disabled) %s' % (id, desc)
      except ValueError as e:
        # bp unparsable
        pass

      #if self.showDetails.setdefault(bp.id, False):
      #  for location in bp:
      #    desc = lldbutil.get_description(location, lldb.eDescriptionLevelFull)
      #    text += '\n  ' + desc

      self.breaks.append(urwid.Text(text))
      self._modified()

    #self.setSelected(selected)

class BreakWin(urwid.ListBox):
  def __init__(self, event_queue, driver):
    self.walker = BreakWalker(driver)
    super(BreakWin, self).__init__(self.walker)
    event_queue.add_listener(self)
    self.driver = driver

  def handle_lldb_event(self, event):
    if lldb.SBBreakpoint.EventIsBreakpointEvent(event):
      self.walker.update()

  #  if isinstance(event, int):
  #    if event == ord('d'):
  #      self.deleteSelected()
  #    if event == curses.ascii.NL or event == curses.ascii.SP:
  #      self.toggleSelected()
  #    elif event == curses.ascii.TAB:
  #      if self.getSelected() != -1:
  #        target = self.driver.getTarget()
  #        if not target.IsValid():
  #          return
  #        i = target.GetBreakpointAtIndex(self.getSelected()).id
  #        self.showDetails[i] = not self.showDetails[i]
  #        self.update()
  #  super(BreakWin, self).handleEvent(event)

  #def toggleSelected(self):
  #  if self.getSelected() == -1:
  #    return
  #  target = self.driver.getTarget()
  #  if not target.IsValid():
  #    return
  #  bp = target.GetBreakpointAtIndex(self.getSelected())
  #  bp.SetEnabled(not bp.IsEnabled())

  #def deleteSelected(self):
  #  if self.getSelected() == -1:
  #    return
  #  target = self.driver.getTarget()
  #  if not target.IsValid():
  #    return
  #  bp = target.GetBreakpointAtIndex(self.getSelected())
  #  target.BreakpointDelete(bp.id)

