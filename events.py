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

    def __eq__(self, other):
        return (self._type == other._type and
                self.value == other.value and
                self.key == other.key and
                self.axis == other.axis)

class MousePositionEvent(Event):
    """
    Set the mouse to a certain position in a given axis.
    >>> mev = MousePositionEvent('X', 10)
    >>> mev.axis
    'x'
    >>> mev.value
    10
    >>> str(mev)
    'mx10'
    >>> mev = MousePositionEvent('y', -10)
    >>> str(mev)
    'my-10'
    >>> mev = MousePositionEvent('a', 10)
    Traceback (most recent call last):
    ValueError: Axis must be x or y
    >>> mev._type == Event.MOUSE_MOVE
    True
    """
    def __init__(self, axis, value):
        axis = axis.lower()
        if axis not in ('x', 'y'):
            raise ValueError("Axis must be x or y")
        super(MousePositionEvent, self).__init__(_type = Event.MOUSE_MOVE,
                                             axis=axis,
                                             value=value)
    def __str__(self):
        return "m%s%d" % (self.axis, self.value)

class MouseMoveEvent(Event):
    """
    Move the mouse to a location. Specify x or y axis.
    >>> mev = MouseMoveEvent('X', 10, 5)
    >>> mev.axis
    'x'
    >>> mev.value
    10
    >>> mev.delta
    5
    >>> str(mev)
    'mx10'
    >>> mev = MouseMoveEvent('y', -10)
    >>> str(mev)
    'my-10'
    >>> mev = MouseMoveEvent('a', 10)
    Traceback (most recent call last):
    ValueError: Axis must be x or y
    >>> mev._type == Event.MOUSE_MOVE
    True
    """
    def __init__(self, axis, value, delta):
        axis = axis.lower()
        self.delta = delta
        if axis not in ('x', 'y'):
            raise ValueError("Axis must be x or y")
        super(MouseMoveEvent, self).__init__(_type = Event.MOUSE_MOVE,
                                             axis=axis,
                                             value=value)
    def __str__(self):
        return "m%s%d" % (self.axis, self.value)

    def __repr__(self):
        return "%s(%s, %d, %d)" % (self.__class__.__name__, self.axis,
                                   self.value, self.delta)


class MouseWheelEvent(Event):
    """
    Move the mouse wheel a given amount
    >>> mwe = MouseWheelEvent(10)
    >>> mwe.value
    10
    >>> mwe._type == Event.MOUSE_WHEEL
    True
    >>> str(mwe)
    'mw10'
    """
    def __init__(self, value):
        super(MouseWheelEvent, self).__init__(_type = Event.MOUSE_WHEEL,
                                             value=value)
    def __str__(self):
        return "mw%d" % self.value

class PressEvent(Event):
    """
    Press a key. Keys 1,2,3 map to mouse 1,2,3

    >>> pe = PressEvent(32)
    >>> pe._type == Event.PRESS
    True
    >>> str(pe)
    'kp32'
    >>> pe = PressEvent('10')
    Traceback (most recent call last):
    ValueError: Key must be an integer
    """
    def __init__(self, key):
        if not type(key) == int:
            raise ValueError('Key must be an integer')
        super(PressEvent, self).__init__(_type = Event.PRESS,
                                         key=key)
    def __str__(self):
        return "kp%d" % self.key

class ReleaseEvent(Event):
    """
    Release a key. Keys 1,2,3 map to mouse 1,2,3
    >>> re = ReleaseEvent(15)
    >>> re._type == Event.RELEASE
    True
    >>> str(re)
    'kr15'
    >>> re = ReleaseEvent('26')
    Traceback (most recent call last):
    ValueError: Key must be an integer
    """
    def __init__(self, key):
        if not type(key) == int:
            raise ValueError('Key must be an integer')
        super(ReleaseEvent, self).__init__(_type = Event.RELEASE,
                                           key=key)
    def __str__(self):
        return "kr%d" % self.key

if __name__ == '__main__':
    import doctest
    print doctest.testmod()

