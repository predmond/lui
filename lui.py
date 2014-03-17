#!/usr/bin/env python
##===-- lui.py -----------------------------------------------*- Python -*-===##
##
##                     The LLVM Compiler Infrastructure
##
## This file is distributed under the University of Illinois Open Source
## License. See LICENSE.TXT for details.
##
##===----------------------------------------------------------------------===##

import lldb
import lldbutil

from optparse import OptionParser
import os
import signal
import sys

import Queue

import debuggerdriver

#import breakwin
import commandwin
import eventwin
#import sourcewin
import statuswin

import urwid

event_queue = None

def test_a_out(driver):
  driver.handleCommand('target create a.out')
  driver.handleCommand('b main')
  driver.handleCommand('run')

def handle_args(driver, argv):
  parser = OptionParser()
  parser.add_option("-p", "--attach", dest="pid", help="Attach to specified Process ID", type="int")
  parser.add_option("-c", "--core", dest="core", help="Load specified core file", type="string")

  (options, args) = parser.parse_args(argv)

  if options.pid is not None:
    try:
      pid = int(options.pid)
      driver.attachProcess(ui, pid)
    except ValueError:
      print "Error: expecting integer PID, got '%s'" % options.pid
  elif options.core is not None:
    if not os.path.exists(options.core):
      raise Exception("Specified core file '%s' does not exist." % options.core)
    driver.loadCore(options.core)
  elif len(args) == 2:
    if not os.path.isfile(args[1]):
      raise Exception("Specified target '%s' does not exist" % args[1])
    driver.createTarget(args[1])
  elif len(args) > 2:
    if not os.path.isfile(args[1]):
      raise Exception("Specified target '%s' does not exist" % args[1])
    driver.createTarget(args[1], args[2:])

def sigint_handler(signal, frame):
  global debugger
  debugger.terminate()

class LLDBView(urwid.WidgetWrap):
  palette = [('body',         'black',      'light gray', 'standout'),
             ('header',       'white',      'dark red',   'bold'),
             ('screen edge',  'light blue', 'dark cyan'),
             ('main shadow',  'dark gray',  'black'),
             ('line',         'black',      'light gray', 'standout'),
             ('bg background','light gray', 'black'),
             ('bg 1',         'black',      'dark blue', 'standout'),
             ('bg 1 smooth',  'dark blue',  'black'),
             ('bg 2',         'black',      'dark cyan', 'standout'),
             ('bg 2 smooth',  'dark cyan',  'black'),
             ('button normal','light gray', 'dark blue', 'standout'),
             ('button select','white',      'dark green'),
             ('line',         'black',      'light gray', 'standout'),
             ('pg normal',    'white',      'black', 'standout'),
             ('pg complete',  'white',      'dark magenta'),
             ('pg smooth',     'dark magenta','black'),
             ('key', 'light cyan', 'black','underline'),
             ('title', 'white', 'black', 'bold'),
             ]

  def __init__(self, event_queue, driver):
    self.event_queue = event_queue
    self.driver = driver
    urwid.WidgetWrap.__init__(self, self.main_window())

  def main_window(self):

    self.status_win = statuswin.StatusWin()
    self.command_win = commandwin.CommandWin(self.driver)
    #self.source_win = sourcewin.SourceWin(self.driver)
    #self.break_win = breakwin.BreakWin(self.driver)
    self.event_win = eventwin.EventWin(self.event_queue)

    def create(w, title):
      return urwid.Frame(body = urwid.AttrWrap(w, 'body'),
                         header = urwid.AttrWrap(urwid.Text(title), 'header'))

    bp = create(urwid.SolidFill(' '), 'Breakpoints')
    st = create(urwid.SolidFill(' '), 'Stacktrace')
    src = create(urwid.SolidFill(' '), 'Source')
    cmd = create(self.command_win, 'Commands')
    evt = create(self.event_win, 'Events')

    top = urwid.SolidFill('1')
    bottom = urwid.SolidFill('2')

    self.frame = urwid.Frame(
      body = urwid.Pile([
               urwid.Columns([
                 ('weight', 2, src),
                 ('weight', 2, urwid.Pile([bp,
                                           st]))
               ]),
               cmd,
               evt]),
      footer = urwid.AttrWrap(self.status_win, 'footer')) 

    return self.frame

class LLDBUI:
  def __init__(self, event_queue, driver):
    #super(LLDBUI, self).__init__(screen, event_queue)

    self.event_queue = event_queue
    self.driver = driver

    self.view = LLDBView(self.event_queue, self.driver)

  def unhandled_input(self, k):
    if k == 'f10':
      self.driver.terminate()
      raise urwid.ExitMainLoop()
    if k == 'f1':
      test_a_out(self.driver)

  def main(self):
    loop = urwid.MainLoop(self.view, self.view.palette,
                          unhandled_input = self.unhandled_input)

    fd = loop.watch_pipe(self.event_queue)
    self.event_queue.set_pipe(fd)

    loop.run()

class LLDBEventQueue:
  def __init__(self):
    self.queue = Queue.Queue()
    self.listeners = []
    self.fd = -1

  def set_pipe(self, fd):
    self.fd = fd

  def add_listener(self, listener):
    self.listeners.append(listener)

  def put(self, event):
    self.queue.put(event)
    if self.fd != -1:
      os.write(self.fd, '1')

  def __call__(self, data):
    while not self.queue.empty():
      event = self.queue.get()
      for listener in self.listeners:
        listener.handle_lldb_event(event)

def main():
  signal.signal(signal.SIGINT, sigint_handler)

  global event_queue
  event_queue = LLDBEventQueue()

  global debugger
  debugger = lldb.SBDebugger.Create()

  driver = debuggerdriver.createDriver(debugger, event_queue)

  view = LLDBUI(event_queue, driver)

  # start the driver thread
  driver.start()

  # hack to avoid hanging waiting for prompts!
  driver.handleCommand("settings set auto-confirm true")

  handle_args(driver, sys.argv)
  view.main()

if __name__ == "__main__":
  print lldb
  main()
