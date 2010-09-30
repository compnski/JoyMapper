import logging
log = logging.getLogger(__name__)
from events import *

class InputFactory(object):
    def __init__(self, event_func):
        self.event_func = event_func

    def StatefulButton(self, key):
        return StatefulButton(self.event_func, key)
    def TwoButtonAxis(self, threshold, pos_key, neg_key):
        return TwoButtonAxis(self.event_func, threshold, pos_key, neg_key)
    def MouseAxis(self, axis, _max, wrap):
        return MouseAxis(self.event_func, axis, _max, wrap)
    def MouseWheelButton(self, value):
        return MouseWheelButton(self.event_func, value)

class Input(object):
    def __init__(self, event_func, key):
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

class StatefulButton(Input):
    """Sends events when state changes"""
    def set_state(self, state):
        if state != self.state:
            ev = PressEvent if state else ReleaseEvent
            self._emit_event(ev(self.key))
        return super(StatefulButton, self).set_state(state)

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
            if state > self.threshold:
                if self.pos_key == None:
                    return
                self.state = 1
                self._emit_event(PressEvent(key=self.pos_key))
            elif state < (-1*self.threshold):
                if self.neg_key == None:
                    return
                self.state = -1
                self._emit_event(PressEvent(key=self.neg_key))
        elif self.state > 0:
            if state < self.threshold:
                self.state = 0
                self._emit_event(ReleaseEvent(key=self.pos_key))
        elif self.state < 0:
            if state > -1*self.threshold:
                self.state = 0
                self._emit_event(ReleaseEvent(key=self.neg_key))

    def tick(self, i):
        pass

class MouseAxis(Input):
    def __init__(self, event_func, axis_name, _max, wrap=True):
        self.event_func = event_func
        self.axis = axis_name
        self.state = 0
        self.pos = _max/2
        self.max = _max
        self.threshold = 0.3
        self.pos_diff = 1
        self.wrap = wrap

    def set_state(self, state):
        if state > self.threshold:
            if self.state < 0:
                self.state = 0
            else:
                self.state = state / self.threshold
        elif state < (-1*self.threshold):
            if self.state > 0:
                self.state = 0
            else:
                self.state = state / self.threshold
        else:
            self.state = 0

    def tick(self, x):
        if (x % 1) == 0:
            if self.state < 0:
                self.pos -= self.pos_diff * (self.state*self.state)
            if self.state > 0:
                self.pos += self.pos_diff * (self.state*self.state)

            if self.wrap:
                self.pos = self.pos % self.max
            else:
                self.pos = min(self.pos, self.max)
                self.pos = max(self.pos, 0)

            if self.state != 0:
                self._emit_event(MouseMoveEvent(axis=self.axis, value=self.pos))

class MouseWheelButton(Input):
    """Sends a click n event for down and that is it"""
    def __init__(self, event_func, value):
        self.value = value
        super(MouseWheelButton, self).__init__(event_func, None)

    def set_state(self, state):
        if state:
            self._emit_event(MouseWheelEvent(self.value))
