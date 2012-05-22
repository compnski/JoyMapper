import Quartz
import events

def mousemove(deltax, deltay, posx, posy):
    event = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (posx, posy),
                                           Quartz.kCGMouseButtonLeft)
    Quartz.CGEventSetIntegerValueField(event,
                                       Quartz.kCGMouseEventDeltaX, deltax)
    Quartz.CGEventSetIntegerValueField(event,
                                       Quartz.kCGMouseEventDeltaY, deltay)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def mouseclick(posx,posy):
    mouseEvent(kCGEventLeftMouseDown, posx,posy)
    mouseEvent(kCGEventLeftMouseUp, posx,posy)


class OsXRelay(object):

    def __init__(self, robot):
        self.mouse_x = 0
        self.mouse_y = 0
        self.robot = robot

    def send(self, event):
        if isinstance(event, events.MouseMoveEvent):
            self._handle_mouse_move(event)
        else:
            self.robot.send(event)

#         if isinstance(event, events.MouseWheelEvent):
#             self._handle_mouse_wheel(event)
#         if isinstance(event, events.PressEvent):
#             self._handle_press_event(event)
#         if isinstance(event, events.ReleaseEvent):
#             self._handle_release_event(event)


    def _handle_mouse_move(self, event):
        deltax, deltay = 0,0
        if event.axis == 'x':
            deltax = event.delta
            self.mouse_x = event.value
        if event.axis == 'y':
            deltay = event.delta
            self.mouse_y = event.value
        mousemove(deltax = deltax, deltay=deltay,
                  posx = self.mouse_x, posy = self.mouse_y)


#     def _handle_press_event(self, event):
#         if event.key in MOUSEMAP:
#             (press_ev, release_ev, button_info) = MOUSEMAP[event.key]
#             win32api.mouse_event(press_ev, 0, 0, button_info)
#         else:
#             win32api.keybd_event(event.key, 0, KEYEVENTF_KEYDOWN)

#     def _handle_release_event(self, event):
#         if event.key in MOUSEMAP:
#             (press_ev, release_ev, button_info) = MOUSEMAP[event.key]
#             win32api.mouse_event(release_ev, 0, 0, button_info)
#         else:
#             win32api.keybd_event(event.key, 0, KEYEVENTF_KEYUP)
