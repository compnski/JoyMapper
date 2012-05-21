import logging
log = logging.getLogger(__name__)
from events import *
from collections import deque

class InputFactory(object):
    def __init__(self, event_func):
        self.event_func = event_func

    def StandardButton(self, key):
        return StandardButton(self.event_func, key)
    def ToggleButton(self, key):
        return ToggleButton(self.event_func, key)
    def DoubleTapButton(self, key):
        return DoubleTapButton(self.event_func, key)
    def TwoButtonAxis(self, threshold, pos_key, neg_key):
        return TwoButtonAxis(self.event_func, threshold, pos_key, neg_key)
    def MouseAxis(self, axis, _max, wrap, **kwargs):
        return MouseAxis(self.event_func, axis, _max, wrap, **kwargs)
    def MouseWheelButton(self, value):
        return MouseWheelButton(self.event_func, value)
    def MultiButton(self, value):
        return MultiButton(self.event_func, value)
#    def RepeatingButton(self, value):
#        return StandardMultiButton(self.event_func, value)
    def KeySequenceButton(self, value):
        return KeySequenceButton(self.event_func, value)
    def Hat(self, buttons):
        return Hat(buttons)

class Hat(object):
    """
    Hat is a special class of input. Instead of emitting events like other
    input, it returns a list of buttons and states which should be processed by
    the controller a second time.

    hat = Hat(
    """
    STATE_OFF = 0
    STATE_ON = 1
    H_UP = 1
    H_DOWN = 0
    H_LEFT = 2
    H_RIGHT = 3
    H_Y = 1
    H_X = 0
    def __init__(self, buttons):
        print "Hat(%s)" % buttons
        self.buttons = map(int,buttons)
        if len(buttons) != 4:
            raise ValueError("Must be passed a 4-value array")
        self.prior_state = (0,0)

    def update_state(self, state):
        buttonList = []
        if state[Hat.H_Y] != self.prior_state[Hat.H_Y]:
            if self.prior_state[Hat.H_Y] == -1:
                buttonList.append((self.buttons[Hat.H_UP], Hat.STATE_OFF))
            elif self.prior_state[Hat.H_Y] == 1:
                buttonList.append((self.buttons[Hat.H_DOWN], Hat.STATE_OFF))
            if state[Hat.H_Y] == -1:
                buttonList.append((self.buttons[Hat.H_UP], Hat.STATE_ON))
            elif state[Hat.H_Y] == 1:
                buttonList.append((self.buttons[Hat.H_DOWN], Hat.STATE_ON))
        if state[Hat.H_X] != self.prior_state[Hat.H_X]:
            if self.prior_state[Hat.H_X] == -1:
                buttonList.append((self.buttons[Hat.H_LEFT], Hat.STATE_OFF))
            elif self.prior_state[Hat.H_X] == 1:
                buttonList.append((self.buttons[Hat.H_RIGHT], Hat.STATE_OFF))
            if state[Hat.H_X] == -1:
                buttonList.append((self.buttons[Hat.H_LEFT], Hat.STATE_ON))
            elif state[Hat.H_X] == 1:
                buttonList.append((self.buttons[Hat.H_RIGHT], Hat.STATE_ON))
        self.prior_state = state
        return buttonList

class Input(object):
    def __init__(self, event_func, key):
        print "Creating input %s(%s)" % (self.__class__.__name__, key)
        self.state = 0
        self.key = key
        self.event_func = event_func
        pass

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def _emit_event(self, ev):
        self.event_func(ev)

class StandardButton(Input):
    """Sends events when state changes"""
    def set_state(self, state):
        if state != self.state:
            ev = PressEvent if state else ReleaseEvent
            self._emit_event(ev(self.key))
            self.state = state

class DoubleTapButton(Input):
    """Sends an extra tap before being pressed. Stays down until released like
    a standard button."""

    def __init__(self, event_func, key):
        super(DoubleTapButton, self).__init__(event_func, key)
        self.event_queue = deque()
        self.tick_mod = 10

    def set_state(self, state):
        if state != self.state:
            if state:
                self.event_queue.append(PressEvent(self.key))
                self.event_queue.append(ReleaseEvent(self.key))
            ev = PressEvent if state else ReleaseEvent
            self.event_queue.append(ev(self.key))
            self.state = state

    def tick(self, i):
        if i % self.tick_mod == 0:
            if self.event_queue:
                self._emit_event(self.event_queue.popleft())

class ToggleButton(Input):
    """Sends events when the state toggles. Each press toggles from
    pressed to released."""
    def set_state(self, state):
        if not self.state and state:
            self._emit_event(PressEvent(self.key))
            self.state = True
        elif self.state and state:
            self._emit_event(ReleaseEvent(self.key))
            self.state = False

class MultiButton(Input):
    """Sends a sequence of key presses when state changes"""
    def __init__(self, event_func, key_list):
        super(MultiButton, self).__init__(event_func, None)
        self.key_list = key_list

    def set_state(self, state):
        if state != self.state:
            ev = PressEvent if state else ReleaseEvent
            for key in self.key_list:
                self._emit_event(ev(key))
            self.state = state

class TwoButtonAxis(Input):
    """Sends one event for positive, one event for negative"""
    def __init__(self, event_func, threshold, pos_key, neg_key):
        super(TwoButtonAxis, self).__init__(event_func, None)
        self.tick_mod = 10 #every 10 ticks
        self.pos_key = pos_key
        self.neg_key = neg_key
        self.threshold = threshold

    def set_state(self, state):
        if self.state == 0:
            if abs(state) >= self.threshold:
                key = self.pos_key if state > 0 else self.neg_key
                if key is None:
                    return
                self.state = state / abs(state)
                self._emit_event(PressEvent(key=key))
        elif 0 <= abs(state) < self.threshold:
            self._emit_event(
                ReleaseEvent(key=self.pos_key
                             if self.state > 0
                             else self.neg_key))
            self.state = 0

    def tick(self, i):
        pass

import pygame
import pygame.mouse

class MouseAxis(Input):
    def __init__(self, event_func, axis_name, _max, wrap=True, tick_mod=1):
        self.event_func = event_func
        self.axis = axis_name
        self.state = 0
        self.pos = _max / 2
        self.max = _max
        self.threshold = 0.3
        self.delta = 1
        self.wrap = wrap
        self.tick_mod = tick_mod

    @property
    def normalized_state(self):
        #TODO -- Make sure this looks right
        return self.state / self.threshold

    def set_state(self, state):
        if  0 <= abs(state) < self.threshold:
            self.state = 0
        else:
            self.state = state

    def tick(self, x):
        if (x % self.tick_mod) != 0:
            return

        move_direction = self.state * abs(self.state)
        delta = (move_direction * self.delta *
                    (self.normalized_state*self.normalized_state))
        prev_pos = self.pos
        self.pos += delta

        if self.wrap:
            self.pos = self.pos % self.max
        else:
            self.pos = min(self.pos, self.max)
            self.pos = max(self.pos, 0)

        if self.state != 0 and delta != 0:
            self._emit_event(
                MouseMoveEvent(axis=self.axis, value=self.pos, delta=delta))

class MouseWheelButton(Input):
    """Sends a click n event for down and that is it"""
    def __init__(self, event_func, value):
        self.value = value
        super(MouseWheelButton, self).__init__(event_func, None)

    def set_state(self, state):
        if state:
            self._emit_event(MouseWheelEvent(self.value))


class KeySequenceButton(Input):
    """Sends a sequence of key press/release events whenever the button is pressed.
    Only fires once per press
    In the config have a comma separated list of buttons
    """
    def __init__(self, event_func, key_list):
        super(KeySequenceButton, self).__init__(event_func, None)
        self.key_list = key_list

    def set_state(self, state):
        if state:
            for key in self.key_list:
                self._emit_event(PressEvent(key))
                self._emit_event(ReleaseEvent(key))


if __name__ == '__main__':
    import doctest
    print doctest.testmod()
