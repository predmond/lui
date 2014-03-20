##===-- commandwin.py ----------------------------------------*- Python -*-===##
##
##                     The LLVM Compiler Infrastructure
##
## This file is distributed under the University of Illinois Open Source
## License. See LICENSE.TXT for details.
##
##===----------------------------------------------------------------------===##

import urwid
import lldb
from itertools import islice

class History(object):
  def __init__(self):
    self.data = {}
    self.pos = 0
    self.tempEntry = ''

  def previous(self, curr):
    if self.pos == len(self.data):
      self.tempEntry = curr

    if self.pos < 0:
      return ''
    if self.pos == 0:
      self.pos -= 1
      return ''
    if self.pos > 0:
      self.pos -= 1
      return self.data[self.pos]

  def next(self):
    if self.pos < len(self.data):
      self.pos += 1

    if self.pos < len(self.data):
      return self.data[self.pos]
    elif self.tempEntry != '':
      return self.tempEntry
    else:
      return ''

  def add(self, c):
    self.tempEntry = ''
    self.pos = len(self.data)
    if self.pos == 0 or self.data[self.pos-1] != c:
      self.data[self.pos] = c
      self.pos += 1

class CommandWalker(urwid.ListWalker):
  def __init__(self):
    self.lines = []
    self.focus = 0

  def output(self, out, attr):
    for line in out.split('\n'):
      text = urwid.AttrWrap(urwid.Text(line), attr)
      self.lines.append(text)
    self.set_focus(len(self.lines)-1)

  def add(self, out):
    self.output(out, 'body')

  def error(self, out):
    self.output(out, 'error')

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
   if len(self.lines) > pos:
     return self.lines[pos], pos
   else:
     return None, None

class CommandEdit(urwid.Edit):
  """ Embed an 'editline'-compatible prompt inside a urwid.Edit widget. """
  def __init__(self, prompt, history, enter_callback, tab_complete_callback):
    self.history = history
    self.enter_callback = enter_callback
    self.tab_complete_callback = tab_complete_callback
    super(CommandEdit, self).__init__(caption = prompt, allow_tab = False)

  def keypress(self, size, key):
    if key == 'enter':
      self.enter_callback(self.get_edit_text())
      self.set_edit_text('')
    elif key == 'tab':
      completion = self.tab_complete_callback(self.get_edit_text())
      if len(completion) > 0:
        self.set_edit_text(self.get_edit_text() + completion)
    #elif key == curses.KEY_DC or key == curses.ascii.DEL or key == curses.ascii.EOT:
    #  self.content = self.content[:self.index] + self.content[self.index+1:]
    #elif key == curses.ascii.VT: # CTRL-K
    #  self.content = self.content[:self.index]
    #elif key == curses.KEY_LEFT or key == curses.ascii.STX: # left or CTRL-B
    #  if self.index > 0:
    #    self.index -= 1
    #elif key == curses.KEY_RIGHT or key == curses.ascii.ACK: # right or CTRL-F
    #  if self.index < len(self.content):
    #    self.index += 1
    #elif key == curses.ascii.SOH: # CTRL-A
    #  self.index = 0
    #elif key == curses.ascii.ENQ: # CTRL-E
    #  self.index = len(self.content)
    elif key == 'up': #or key == curses.ascii.DLE: # up or CTRL-P
      self.set_edit_text(self.history.previous(self.get_edit_text()))
      #self.index = len(self.content)
    elif key == 'down': # or key == curses.ascii.SO: # down or CTRL-N
      self.set_edit_text(self.history.next())
      #self.index = len(self.content)
    else:
      return super(CommandEdit, self).keypress(size, key)
    return None

class CommandWin(urwid.Frame):
  def __init__(self, driver):
    self.command = ""
    self.data = ""
    #driver.setSize(w, h)
    self.driver = driver
    self.history = History()

    self.walker = CommandWalker()
    self.output = urwid.ListBox(self.walker)

    def enter_callback(content):
      self.handle_command(content)

    def tab_complete_callback(content):
      self.data = content
      matches = lldb.SBStringList()
      commandinterpreter = self.driver.getCommandInterpreter()
      commandinterpreter.HandleCompletion(self.data, len(self.data), 0, -1, matches)
      if matches.GetSize() == 2:
        return matches.GetStringAtIndex(0)
      else:
        self.walker.add("Available Completions:")
        for m in islice(matches, 1, None):
          self.walker.add(m)
        return ''

    self.edit = CommandEdit(self.driver.getPrompt(),
                            self.history,
                            enter_callback,
                            tab_complete_callback)

    super(CommandWin, self).__init__(body = self.output, footer = self.edit)

    self.handle_command('version')

  def handle_command(self, cmd):
    # enter!
    if cmd == '':
      cmd = self.history.previous('')
    elif cmd in ('q', 'quit'):
      self.driver.terminate()
      return

    self.history.add(cmd)
    ret = self.driver.handleCommand(cmd)
    if ret.Succeeded():
      out = ret.GetOutput()
      self.walker.add(out)
    else:
      out = ret.GetError()
      self.walker.error(out)
