import events
import inputs
win32api = None
try:
    import win32api
except ImportError:
    class MissingWin32Api(object):
        def __getattr__(self, key):
            raise ImportError("Win32 API not supported on this system. "
                              "Please install or use RelayBot")
    win32api = MissingWin32Api()

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_XDOWN = 0x0080 # Pass button number as third arg
MOUSEEVENTF_XUP = 0x0100 # Pass button number as third arg
KEYEVENTF_KEYDOWN = 0x0
KEYEVENTF_KEYUP = 0x2


MOUSEMAP = {1001:(MOUSEEVENTF_LEFTDOWN,
                  MOUSEEVENTF_LEFTUP, 0),
            1002:(MOUSEEVENTF_RIGHTDOWN,
                  MOUSEEVENTF_RIGHTUP, 0),
            1003:(MOUSEEVENTF_MIDDLEDOWN,
                  MOUSEEVENTF_MIDDLEUP, 0),
            1004:(MOUSEEVENTF_XDOWN,
                  MOUSEEVENTF_XUP, 1),
            1005:(MOUSEEVENTF_XDOWN,
                  MOUSEEVENTF_XUP, 2),
            }

class Win32Relay(object):
    """
    Sends Win32 mouse and keyboard events.
    send(events.Event) dispatches events based on type.
    """

    def __init__(self, _):
        self.mouse_x = 0
        self.mouse_y = 0

    def send(self, event):
        if isinstance(event, events.MouseMoveEvent):
            self._handle_mouse_move(event)
        if isinstance(event, events.MouseWheelEvent):
            self._handle_mouse_wheel(event)
        if isinstance(event, events.PressEvent):
            self._handle_press_event(event)
        if isinstance(event, events.ReleaseEvent):
            self._handle_release_event(event)

    def _handle_press_event(self, event):
        if event.key in MOUSEMAP:
            (press_ev, release_ev, button_info) = MOUSEMAP[event.key]
            win32api.mouse_event(press_ev, 0, 0, button_info)
        else:
            win32api.keybd_event(event.key, 0, KEYEVENTF_KEYDOWN)

    def _handle_release_event(self, event):
        if event.key in MOUSEMAP:
            (press_ev, release_ev, button_info) = MOUSEMAP[event.key]
            win32api.mouse_event(release_ev, 0, 0, button_info)
        else:
            win32api.keybd_event(event.key, 0, KEYEVENTF_KEYUP)

    def _handle_mouse_wheel(self, event):
        win32api.mouse_event(MOUSEEVENTF_WHEEL, 0,0, -1 * event.value)

    # def _handle_mouse_position(self, data):
    #     mx, my = 0,0
    #     if event.axis == 'x':
    #         mx = event.value
    #     if event.axis == 'y':
    #         my = event.value
    #     win32api.mouse_event(MOUSEEVENTF_ABSOLUTE, mx, my)

    def _handle_mouse_move(self, event):
        mx, my = 0,0
        if event.axis == 'x':
            mx = event.delta
        if event.axis == 'y':
            my = event.delta
        print "mousemove(%s, %d, %d)" % (event.axis, mx, my)
        win32api.mouse_event(MOUSEEVENTF_MOVE, int(mx), int(my))
