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


class CommandWin(urwid.Frame):
  def __init__(self, driver):
    self.command = ""
    self.data = ""
    #driver.setSize(w, h)

    self.walker = CommandWalker()
    self.output = urwid.ListBox(self.walker)
    self.edit = urwid.Edit(caption = '(lldb) ',
                           allow_tab = False)

    self.driver = driver
    self.history = History()

    super(CommandWin, self).__init__(body = self.output, footer = self.edit)

  def keypress(self, size, key):
    if key == 'enter':
      cmd = self.edit.get_edit_text()
      self.edit.set_edit_text('')
      self.handleCommand(cmd)
    super(CommandWin, self).keypress(size, key)

  #  def enterCallback(content):
  #    self.handleCommand(content)

  #  def tabCompleteCallback(content):
  #    self.data = content
  #    matches = lldb.SBStringList()
  #    commandinterpreter = self.getCommandInterpreter()
  #    commandinterpreter.HandleCompletion(self.data, self.el.index, 0, -1, matches)
  #    if matches.GetSize() == 2:
  #      self.el.content += matches.GetStringAtIndex(0)
  #      self.el.index = len(self.el.content)
  #      self.el.draw()
  #    else:
  #      self.win.move(self.el.starty, self.el.startx)
  #      self.win.scroll(1)
  #      self.win.addstr("Available Completions:")
  #      self.win.scroll(1)
  #      for m in islice(matches, 1, None):
  #        self.win.addstr(self.win.getyx()[0], 0, m)
  #        self.win.scroll(1)
  #      self.el.draw()

  #  self.startline = self.win.getmaxyx()[0]-2

  #  self.el = cui.CursesEditLine(self.win, self.history, enterCallback, tabCompleteCallback)
  #  self.el.prompt = self.driver.getPrompt()
  #  self.el.showPrompt(self.startline, 0)

  def handleCommand(self, cmd):
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
      #attr = curses.A_NORMAL
    else:
      out = ret.GetError()
      self.walker.error(out)
      #attr = curses.color_pair(3) # red on black
    #self.win.addstr(self.startline, 0, out + '\n', attr)

  #def handleEvent(self, event):
  #  if isinstance(event, int):
  #    if event == curses.ascii.EOT and self.el.content == '':
  #      # When the command is empty, treat CTRL-D as EOF.
  #      self.driver.terminate()
  #      return
  #    self.el.handleEvent(event)

  def getCommandInterpreter(self):
    return self.driver.getCommandInterpreter()
