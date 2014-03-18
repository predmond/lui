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

import argparse
import os
import signal
import sys

import Queue

import debuggerdriver

import statuswin
import layout
import urwid

event_queue = None
debug = False

def test_a_out(driver):
  driver.handleCommand('target create a.out')
  driver.handleCommand('b main')
  driver.handleCommand('run')

def handle_args(driver, argv):
  parser = argparse.ArgumentParser(description='LLDB Terminal User Interface')
  parser.add_argument("-p", "--attach", dest="pid", type=int,
                      help="Attach to specified Process ID")
  parser.add_argument("-c", "--core",
                      help="Load specified core file")
  parser.add_argument("-d", "--debug", action='store_true',
                      help="Enable lui debugging")
  parser.add_argument("--default_layout", action='store_true',
                      help="Dump default layout")
  parser.add_argument('target', nargs='*',
                      help="debug target")

  args = parser.parse_args()

  if args.default_layout:
    print layout.default_layout
    sys.exit(0)
  #if args.layout is not None:
  layout.load_layout()

  global debug
  debug = args.debug

  if args.pid is not None:
    driver.attachProcess(args.pid)
  elif args.core is not None:
    if not os.path.exists(args.core):
      raise Exception("Specified core file '%s' does not exist." % args.core)
    driver.loadCore(options.core)
  elif len(args.target) > 0:
    target = args.target[0]
    target_args = args.target[1:]
    if not os.path.isfile(target):
      raise Exception("Specified target '%s' does not exist" % target)
    driver.createTarget(target, target_args)

def sigint_handler(signal, frame):
  global debugger
  debugger.terminate()

class LLDBView(urwid.WidgetWrap):
  palette = [('body',         'black',      'light gray', 'standout'),
             ('error',        'dark red',   'light gray', 'standout'),
             ('header',       'white',      'dark blue',   'bold'),
             ('key', 'light cyan', 'black','underline'),
             ('title', 'white', 'black', 'bold'),
             ]

  def __init__(self, event_queue, driver):
    self.event_queue = event_queue
    self.driver = driver
    urwid.WidgetWrap.__init__(self, self.main_window())

  def main_window(self):

    self.status_win = statuswin.StatusWin()

    builder = layout.LayoutBuilder(self.event_queue, self.driver)
    w = builder.build(layout.loaded_layout['default'])

    self.frame = urwid.Frame(body = w, footer = urwid.AttrWrap(self.status_win, 'footer')) 
    return self.frame

class LLDBUI:
  def __init__(self, event_queue, driver):
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

  handle_args(driver, sys.argv)

  view = LLDBUI(event_queue, driver)

  # start the driver thread
  driver.start()

  # hack to avoid hanging waiting for prompts!
  driver.handleCommand("settings set auto-confirm true")

  view.main()

if __name__ == "__main__":
  print lldb
  main()
