import events

import unittest
from collections import defaultdict

class MockWin32Api(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.x, self.y = 0, 0
        self.wheel = 0
        self.button_state = defaultdict(bool)
        self.key_state = defaultdict(bool)


    def mouse_event(self, type_, x, y , button_info = None):
        if type_ == win32_relay.MOUSEEVENTF_MOVE:
            self.x, self.y = self.x + x, self.y + y
        elif type_ == win32_relay.MOUSEEVENTF_LEFTDOWN:
            if self.button_state['left']:
                raise Exception("Left mouse button already down.")
            self.button_state['left'] = True
        elif type_ == win32_relay.MOUSEEVENTF_LEFTUP:
            if not self.button_state['left']:
                raise Exception("Left mouse button already up.")
            self.button_state['left'] = False
        elif type_ == win32_relay.MOUSEEVENTF_RIGHTDOWN:
            if self.button_state['right']:
                raise Exception("Right mouse button already down.")
            self.button_state['right'] = True
        elif type_ == win32_relay.MOUSEEVENTF_RIGHTUP:
            if not self.button_state['right']:
                raise Exception("Right mouse button already up.")
            self.button_state['right'] = False
        elif type_ == win32_relay.MOUSEEVENTF_MIDDLEDOWN:
            if self.button_state['middle']:
                raise Exception("Middle mouse button already down.")
            self.button_state['middle'] = True
        elif type_ == win32_relay.MOUSEEVENTF_MIDDLEUP:
            if not self.button_state['middle']:
                raise Exception("Middle mouse button already up.")
            self.button_state['middle'] = False
        elif type_ == win32_relay.MOUSEEVENTF_XDOWN:
            if self.button_state[button_info]:
                raise Exception("Extra button %d already down." % button_info)
            self.button_state[button_info] = True
        elif type_ == win32_relay.MOUSEEVENTF_XUP:
            if not self.button_state[button_info]:
                raise Exception("Extra button %d already up." % button_info)
            self.button_state[button_info] = False
        elif type_ == win32_relay.MOUSEEVENTF_WHEEL:
            self.wheel += button_info

    def keybd_event(self, key, flags, type_):
        prev_state = self.key_state[key]
        self.key_state[key] = (True if type_ is win32_relay.KEYEVENTF_KEYDOWN
                               else False)
        if prev_state == self.key_state[key]:
            raise Exception("Got duplicate event %d for key %s" % type_, key)

import win32_relay
win32_relay.win32api = win32api = MockWin32Api()

class TestWin32Relay(unittest.TestCase):

    def setUp(self):
        win32api.reset()
        self.relay = win32_relay.Win32Relay('')

    def test_press_event(self):
        self.assertEqual(False, win32api.key_state[32])
        self.relay._handle_press_event(events.PressEvent(32))
        self.assertEqual(True, win32api.key_state[32])

        self.assertEqual(False, win32api.button_state['left'])
        self.relay._handle_press_event(events.PressEvent(1001))
        self.assertEqual(True, win32api.button_state['left'])

        self.assertEqual(False, win32api.button_state['right'])
        self.relay._handle_press_event(events.PressEvent(1002))
        self.assertEqual(True, win32api.button_state['right'])

        self.assertEqual(False, win32api.button_state['middle'])
        self.relay._handle_press_event(events.PressEvent(1003))
        self.assertEqual(True, win32api.button_state['middle'])

        self.assertEqual(False, win32api.button_state[1])
        self.relay._handle_press_event(events.PressEvent(1004))
        self.assertEqual(True, win32api.button_state[1])

        self.assertEqual(False, win32api.button_state[2])
        self.relay._handle_press_event(events.PressEvent(1005))
        self.assertEqual(True, win32api.button_state[2])

    def test_release_event(self):
        win32api.key_state[32] = True
        self.relay._handle_release_event(events.ReleaseEvent(32))
        self.assertEqual(False, win32api.key_state[32])

        win32api.button_state['left'] = True
        self.relay._handle_release_event(events.ReleaseEvent(1001))
        self.assertEqual(False, win32api.button_state['left'])

        win32api.button_state['right'] = True
        self.relay._handle_release_event(events.ReleaseEvent(1002))
        self.assertEqual(False, win32api.button_state['right'])

        win32api.button_state['middle'] = True
        self.relay._handle_release_event(events.ReleaseEvent(1003))
        self.assertEqual(False, win32api.button_state['middle'])

        win32api.button_state[1] = True
        self.relay._handle_release_event(events.ReleaseEvent(1004))
        self.assertEqual(False, win32api.button_state[1])

        win32api.button_state[2] = True
        self.relay._handle_release_event(events.ReleaseEvent(1005))
        self.assertEqual(False, win32api.button_state[2])

    def test_mouse_move(self):
        self.assertEqual(0, win32api.x)
        self.assertEqual(0, win32api.y)
        self.relay._handle_mouse_move(events.MouseMoveEvent('x', 12, 12))
        self.assertEqual(12, win32api.x)
        self.assertEqual(0, win32api.y)
        self.relay._handle_mouse_move(events.MouseMoveEvent('x', 24, 12))
        self.assertEqual(24, win32api.x)
        self.assertEqual(0, win32api.y)

        self.relay._handle_mouse_move(events.MouseMoveEvent('y', 30, 30))
        self.assertEqual(24, win32api.x)
        self.assertEqual(30, win32api.y)

        self.relay._handle_mouse_move(events.MouseMoveEvent('x', 14, -10))
        self.assertEqual(14, win32api.x)
        self.assertEqual(30, win32api.y)

    def test_mouse_wheel(self):
        self.assertEqual(0, win32api.wheel)
        self.relay._handle_mouse_wheel(events.MouseWheelEvent(4))
        self.assertEqual(-4, win32api.wheel)
        self.relay._handle_mouse_wheel(events.MouseWheelEvent(-4))
        self.assertEqual(0, win32api.wheel)

if __name__ == '__main__':
    unittest.main()
