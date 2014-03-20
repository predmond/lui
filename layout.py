import urwid
import breakwin
import commandwin
import eventwin
import sourcewin

default_layout = """
{
  "default" :
  {
    "cols" : [
      { "rows" : [ "source", "command" ] },
      { "rows" : [
          { "cols" : [ "breakpoints", "threads" ] },
          { "cols" : [ "backtrace", "events" ] }
        ]
      }
    ]
  }
}
"""

loaded_layout = None

def load_layout(json_layout = None):
  import json
  if json_layout is None:
    json_layout = default_layout
  global loaded_layout
  loaded_layout = json.loads(json_layout)

class LayoutBuilder:
  def __init__(self, event_queue, driver):
    self.event_queue = event_queue
    self.driver = driver

  def layout_error(self, msg):
    print 'layout error:', msg
    sys.exit(0)
  
  def build_cols(self, obj):
    if not isinstance(obj, list) or len(obj) < 1:
      self.layout_error('cols object requires array of at least one item')
    objs = [self.build_layout(x) for x in obj]
    return urwid.Columns(objs)
  
  def build_rows(self, obj):
    if not isinstance(obj, list) or len(obj) < 1:
      self.layout_error('rows object requires array of at least one item')
    objs = [self.build_layout(x) for x in obj]
    return urwid.Pile(objs)
  
  def build_view(self, obj):
    def create(w, title):
      w = urwid.Columns([w, ('fixed', 1, urwid.SolidFill(u'|'))])
      w = urwid.AttrWrap(w, 'body')
      return urwid.Frame(body = w,
                         header = urwid.AttrWrap(urwid.Text(title), 'header', 'title'))
    if obj == 'source':
      return create(sourcewin.SourceWin(self.event_queue, self.driver), 'Source')
    elif obj == 'command':
      return create(commandwin.CommandWin(self.driver), 'Commands')
    elif obj == 'breakpoints':
      return create(breakwin.BreakWin(self.event_queue, self.driver), 'Breakpoints')
    elif obj == 'threads':
      return create(urwid.SolidFill(u' '), 'Threads')
    elif obj == 'backtrace':
      return create(urwid.SolidFill(u' '), 'Backtrace')
    elif obj == 'events':
      return create(eventwin.EventWin(self.event_queue), 'LLDB Events')
    elif obj == 'terminal':
      return create(urwid.Terminal(None), 'Terminal')
    else:
      self.layout_error('unexpected object %s' % obj)
  
  def build_layout(self, obj):
    if isinstance(obj, dict):
      if len(obj.keys()) != 1:
        self.layout_error('single object expected')
      key = obj.keys()[0]
      obj = obj[key]
      if key == 'rows':
        return self.build_rows(obj)
      elif key == 'cols':
        return self.build_cols(obj)
      else:
        self.layout_error('unexpected object %s' % key)
    elif isinstance(obj, list):
      return [self.build_layout(x) for x in obj]
    elif isinstance(obj, basestring):
      return self.build_view(obj)
    else:
      self.layout_error('unexpected object %s' % (obj))
  
  def build(self, obj):
    if not isinstance(obj, dict) or len(obj.keys()) != 1:
      self.layout_error('single object required')
    key = obj.keys()[0]
    if key != 'cols' and key != 'rows':
      self.layout_error('invalid top-level object %s' % key)
    return self.build_layout(obj)

