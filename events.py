class Event(object):
    MOUSE_MOVE = 0
    MOUSE_WHEEL = 1
    PRESS = 2
    RELEASE = 3
    def __init__(self, _type, key=None, value=None, axis=None):
        """Type of event can be MOUSE_MOVE, MOUSE_WHEEL, PRESS, or RELEASE.
        Use value for distances, (MOUSE_MOVE, MOUSE_WHEEL)
        Use key for PRESS and RELEASE
        """
        self._type = _type
        self.value = value
        self.key = key
        self.axis = axis

class MouseMoveEvent(Event):
    """Move the mouse to a location. Specify x or y axis."""
    def __init__(self, axis, value):
        axis = axis.lower()
        if axis not in ('x', 'y'):
            raise ValueError("Axis must be x or y")
        super(MouseMoveEvent, self).__init__(_type = Event.MOUSE_MOVE,
                                             axis=axis,
                                             value=value)
    def __str__(self):
        return "m%s%d" % (self.axis, self.value)

class MouseWheelEvent(Event):
    """Move the mouse wheel a given amount"""
    def __init__(self, value):
        super(MouseWheelEvent, self).__init__(_type = Event.MOUSE_WHEEL,
                                             value=value)
    def __str__(self):
        return "mw%d" % self.value

class PressEvent(Event):
    """Press a key. Keys 1,2,3 map to mouse 1,2,3"""
    def __init__(self, key):
        super(PressEvent, self).__init__(_type = Event.PRESS,
                                         key=key)
    def __str__(self):
        print self.key
        return "kp%d" % self.key

class ReleaseEvent(Event):
    """Release a key. Keys 1,2,3 map to mouse 1,2,3"""
    def __init__(self, key):
        super(ReleaseEvent, self).__init__(_type = Event.RELEASE,
                                           key=key)
    def __str__(self):
        return "kr%d" % self.key
