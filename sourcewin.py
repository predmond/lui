##===-- sourcewin.py -----------------------------------------*- Python -*-===##
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
import os

class SourceWalker(urwid.ListWalker):
  def __init__(self):
    self.focus = 0
    self.lines = []

  def message(self, msg):
    w = urwid.Text('\n[ %s ]' % msg, align='center')
    self.lines = [w]
    self._modified()

  def set_unavailable(self, msg = 'Source information unavailable'):
    self.message(msg)

  def set_filepath(self, path):
    self.lines = []
    lines = []
    try:
      with open(path) as f:
        lines = [line.rstrip('\r\n') for line in f]
    except IOError as e:
      self.set_unavailable(e.strerror)
      return

    #try:
    #  from pygments.lexers import get_lexer_for_filename
    #  from pygments.formatter import Formatter

    #  class UrwidFormatter(Formatter):
    #    def convert(self, color):
    #      r = int(color[:2], 16)
    #      g = int(color[2:4], 16)
    #      b = int(color[4:], 16)
    #      r = urwid.util.int_scale(r, 255, 6)
    #      g = urwid.util.int_scale(r, 255, 6)
    #      b = urwid.util.int_scale(r, 255, 6)
    #      return '#%x%x%x' % (r, g, b)

    #    def __init__(self, **options):
    #      Formatter.__init__(self, **options)
    #      self.text = []
    #      # create a dict of (start, end) tuples that wrap the
    #      # value of a token so that we can use it in the format
    #      # method later
    #      self.styles = {}

    #      # we iterate over the `_styles` attribute of a style item
    #      # that contains the parsed style values.
    #      for token, style in self.style:
    #        start = "(urwid.AttrSpec('"
    #        # a style item is a tuple in the following form:
    #        # colors are readily specified in hex: 'RRGGBB'
    #        if style['color']:
    #          start += self.convert(style['color'])
    #          #end = '</font>' + end
    #        else:
    #          start += "default"

    #        if style['bold']:
    #          start += ', bold'
    #        if style['underline']:
    #          start += ', underline'
    #        start += "', 'default', 256), '"

    #        end = "'), "

    #        self.styles[token] = (start, end)

    #    def format(self, tokensource, outfile):
    #      # lastval is a string we use for caching
    #      # because it's possible that an lexer yields a number
    #      # of consecutive tokens with the same token type.
    #      # to minimize the size of the generated html markup we
    #      # try to join the values of same-type tokens here
    #      lastval = ''
    #      lasttype = None
    #
    #      outfile.write('[')
    #
    #      for ttype, value in tokensource:
    #        value = value.rstrip('\r\n')
    #        # if the token type doesn't exist in the stylemap
    #        # we try it with the parent of the token type
    #        # eg: parent of Token.Literal.String.Double is
    #        # Token.Literal.String
    #        while ttype not in self.styles:
    #          ttype = ttype.parent
    #        if ttype == lasttype:
    #          # the current token type is the same of the last
    #          # iteration. cache it
    #          lastval += value
    #        else:
    #          # not the same token as last iteration, but we
    #          # have some data in the buffer. wrap it with the
    #          # defined style and write it to the output file
    #          if lastval:
    #            stylebegin, styleend = self.styles[lasttype]
    #            outfile.write(stylebegin + lastval + styleend)
    #          # set lastval/lasttype to current values
    #          lastval = value
    #          lasttype = ttype
    #
    #      # if something is left in the buffer, write it to the
    #      # output file, then close the opened <pre> tag
    #      if lastval:
    #        stylebegin, styleend = self.styles[lasttype]
    #        outfile.write(stylebegin + lastval + styleend)

    #      outfile.write(']')

    #  lexer = get_lexer_for_filename(filename)
    #  formatter = UrwidFormatter()

    #  from pygments import highlight
    #  for line in lines:
    #    line = highlight(line, lexer, formatter)
    #    text = eval(line)
    #    #self.lines.append(urwid.Text(line))
    #    if len(text) > 0:
    #      self.lines.append(urwid.Text(text))
    #    else:
    #      self.lines.append(urwid.Text(''))

    #except ImportError:
    #  pass

    for lineno, line in enumerate(lines):
      self.lines.append(urwid.Text('%4d | %s' % (lineno + 1, line)))

    self._modified()

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

class SourceWin(urwid.ListBox):
  def __init__(self, event_queue, driver):
    self.walker = SourceWalker()
    super(SourceWin, self).__init__(self.walker)
    event_queue.add_listener(self)
    self.sourceman = driver.getSourceManager()
    self.sources = {}

    self.filename= None
    self.pc_line = None
    self.viewline = 0

    self.breakpoints = { }

    self.markerPC = ":) "
    self.markerBP = "B> "
    self.markerNone  = "   "

    # FIXME: syntax highlight broken
    self.formatter = None
    self.lexer = None

  def handle_lldb_event(self, event):
    if lldb.SBBreakpoint.EventIsBreakpointEvent(event):
      self.handle_bp_event(event)
    if lldb.SBProcess.EventIsProcessEvent(event) and \
        not lldb.SBProcess.GetRestartedFromEvent(event):
      process = lldb.SBProcess.GetProcessFromEvent(event)
      if not process.IsValid():
        return
      if process.GetState() == lldb.eStateStopped:
        self.refresh_source(process)
      elif process.GetState() == lldb.eStateExited:
        self.notify_exited(process)
    if lldb.SBThread.EventIsThreadEvent(event):
      thread = lldb.SBThread.GetThreadFromEvent(event)
      self.refresh_source(thread.process)
      #self.walker.message(str(event))

  def notify_exited(self, process):
    target = lldbutil.get_description(process.GetTarget())
    pid = process.GetProcessID()
    ec = process.GetExitStatus()
    self.walker.message("Process %s [%d] has exited with exit-code %d" % (target, pid, ec))

  def refresh_source(self, process = None):
    if process is not None:
      loc = process.GetSelectedThread().GetSelectedFrame().GetLineEntry()
      f = loc.GetFileSpec()
      self.pc_line = loc.GetLine()

      if not f.IsValid():
        self.walker.set_unavailable()
        return

      self.filename = f.GetFilename()
      path = os.path.join(f.GetDirectory(), self.filename)
      self.walker.set_filepath(path)

#  def formatContent(self, content, pc_line, breakpoints):
#    source = ""
#    count = 1
#    self.win.erase()
#    end = min(len(content), self.viewline + self.height)
#    for i in range(self.viewline, end):
#      line_num = i + 1
#      marker = self.markerNone
#      attr = curses.A_NORMAL
#      if line_num == pc_line:
#        attr = curses.A_REVERSE
#      if line_num in breakpoints:
#        marker = self.markerBP
#      line = "%s%3d %s" % (marker, line_num, self.highlight(content[i]))
#      if len(line) >= self.width:
#        line = line[0:self.width-1] + "\n"
#      self.win.addstr(line, attr)
#      source += line
#      count = count + 1
#    return source
#
#  def addBPLocations(self, locations):
#    for path in locations:
#      lines = locations[path]
#      if path in self.breakpoints:
#        self.breakpoints[path].update(lines)
#      else:
#        self.breakpoints[path] = lines
#
#  def removeBPLocations(self, locations):
#    for path in locations:
#      lines = locations[path]
#      if path in self.breakpoints:
#        self.breakpoints[path].difference_update(lines)
#      else:
#        raise "Removing locations that were never added...no good"
#
  def handle_bp_event(self, event):
    def getLocations(event):
      locs = {}

      bp = lldb.SBBreakpoint.GetBreakpointFromEvent(event)

      if bp.IsInternal():
        # don't show anything for internal breakpoints
        return

      for location in bp:
        # hack! getting the LineEntry via SBBreakpointLocation.GetAddress.GetLineEntry does not work good for
        # inlined frames, so we get the description (which does take into account inlined functions) and parse it.
        desc = lldbutil.get_description(location, lldb.eDescriptionLevelFull)
        match = re.search('at\ ([^:]+):([\d]+)', desc)
        try:
          path = match.group(1)
          line = int(match.group(2).strip())
        except ValueError as e:
          # bp loc unparsable
          continue

        if path in locs:
          locs[path].add(line)
        else:
          locs[path] = set([line])
      return locs

    #event_type = lldb.SBBreakpoint.GetBreakpointEventTypeFromEvent(event)
    #if event_type == lldb.eBreakpointEventTypeEnabled \
    #    or event_type == lldb.eBreakpointEventTypeAdded \
    #    or event_type == lldb.eBreakpointEventTypeLocationsResolved \
    #    or event_type == lldb.eBreakpointEventTypeLocationsAdded:
    #  self.addBPLocations(getLocations(event))
    #elif event_type == lldb.eBreakpointEventTypeRemoved \
    #    or event_type == lldb.eBreakpointEventTypeLocationsRemoved \
    #    or event_type == lldb.eBreakpointEventTypeDisabled:
    #  self.removeBPLocations(getLocations(event))
    #elif event_type == lldb.eBreakpointEventTypeCommandChanged \
    #    or event_type == lldb.eBreakpointEventTypeConditionChanged \
    #    or event_type == lldb.eBreakpointEventTypeIgnoreChanged \
    #    or event_type == lldb.eBreakpointEventTypeThreadChanged \
    #    or event_type == lldb.eBreakpointEventTypeInvalidType:
    #  # no-op
    #  pass
    self.refresh_source()
