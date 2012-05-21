import unittest2 as unittest
import inputs
import events

class HatTest(unittest.TestCase):
    def setUp(self):
        self.hat = inputs.Hat(['10', '15', '20', '25'])

    def testBadCtor(self):
        self.assertRaises(ValueError, inputs.Hat, ([]))
        self.assertRaises(ValueError, inputs.Hat, ([1]))
        self.assertRaises(ValueError, inputs.Hat, ([1,2]))
        self.assertRaises(ValueError, inputs.Hat, ([1,2,3]))
        self.assertRaises(ValueError, inputs.Hat, ([1,2,3,4,5]))

        self.assertRaises(ValueError, inputs.Hat, (['1','2','3','a']))

    def testY(self):
        self.assertEqual([], self.hat.update_state((0, 0)))
        self.assertEqual([(10, inputs.Hat.STATE_ON)],
                         self.hat.update_state((0, 1)))
        self.assertEqual([(10, inputs.Hat.STATE_OFF)],
                         self.hat.update_state((0, 0)))
        self.assertEqual([(15, inputs.Hat.STATE_ON)],
                         self.hat.update_state((0, -1)))
        self.assertEqual([(15, inputs.Hat.STATE_OFF), (10, inputs.Hat.STATE_ON)],
                         self.hat.update_state((0, 1)))
        self.assertEqual([(10, inputs.Hat.STATE_OFF)],
                         self.hat.update_state((0, 0)))

    def testX(self):
        self.assertEqual([], self.hat.update_state((0, 0)))
        self.assertEqual([(25, inputs.Hat.STATE_ON)],
                         self.hat.update_state((1, 0)))
        self.assertEqual([(25, inputs.Hat.STATE_OFF)],
                         self.hat.update_state((0, 0)))
        self.assertEqual([(20, inputs.Hat.STATE_ON)],
                         self.hat.update_state((-1, 0)))
        self.assertEqual([(20, inputs.Hat.STATE_OFF), (25, inputs.Hat.STATE_ON)],
                         self.hat.update_state((1, 0)))
        self.assertEqual([(25, inputs.Hat.STATE_OFF)],
                         self.hat.update_state((0, 0)))


class InputUnitTest(unittest.TestCase):
    "Unit test for all Input games"
    def setUp(self):
        self.events = []
        self.KEY = 35

    def _eventFunc(self, ev):
        self.events.append(ev)

    def assertEvents(self, events):
        "Check that the passed in events were sent. Clears the seen events"
        self.assertEqual(events, self.events)
        self.clearEvents()

    def clearEvents(self):
        self.events = []

    def getOnlyEvent(self):
        self.assertEqual(1, len(self.events))
        evt = self.events[0]
        self.clearEvents()
        return evt


class StandardButtonTest(InputUnitTest):
    def setUp(self):
        super(StandardButtonTest, self).setUp()
        self.button = inputs.StandardButton(self._eventFunc, self.KEY)

    def testPress(self):
        self.button.set_state(True)
        self.assertEvents([events.PressEvent(self.KEY)])

    def testPressAndRelease(self):
        self.button.set_state(True)
        self.button.set_state(False)
        self.assertEvents([events.PressEvent(self.KEY),
                           events.ReleaseEvent(self.KEY)])


class DoubleTapButtonTest(InputUnitTest):
    def setUp(self):
        super(DoubleTapButtonTest, self).setUp()
        self.button = inputs.DoubleTapButton(self._eventFunc, self.KEY)

    def testPress(self):
        self.button.set_state(True)
        self.button.tick(10)
        self.button.tick(20)
        self.button.tick(30)
        self.assertEvents([events.PressEvent(self.KEY),
                           events.ReleaseEvent(self.KEY),
                           events.PressEvent(self.KEY)])

    def testPressAndRelease(self):
        self.button.set_state(True)
        self.button.tick(10)
        self.button.tick(20)
        self.button.tick(30)
        self.button.set_state(False)
        self.button.tick(10)
        self.button.tick(20)
        self.button.tick(30)
        self.assertEvents([events.PressEvent(self.KEY),
                           events.ReleaseEvent(self.KEY),
                           events.PressEvent(self.KEY),
                           events.ReleaseEvent(self.KEY)])

class ToggleButtonTest(InputUnitTest):
    def setUp(self):
        super(ToggleButtonTest, self).setUp()
        self.button = inputs.ToggleButton(self._eventFunc, self.KEY)

    def testPress(self):
        self.button.set_state(True)
        self.assertEvents([events.PressEvent(self.KEY)])

    def testPressAndRelease(self):
        self.button.set_state(True)
        self.button.set_state(False)
        self.assertEvents([events.PressEvent(self.KEY)])

    def testPressAndReleaseTwice(self):
        self.button.set_state(True)
        self.button.set_state(False)
        self.button.set_state(True)
        self.button.set_state(False)
        self.assertEvents([events.PressEvent(self.KEY),
                           events.ReleaseEvent(self.KEY)])

class MultiButtonTest(InputUnitTest):

    def setUp(self):
        super(MultiButtonTest, self).setUp()
        self.keys = [1, 2, 3, 4, 10]
        self.button = inputs.MultiButton(self._eventFunc, self.keys)

    def testPress(self):
        self.button.set_state(True)
        self.assertEvents(map(events.PressEvent, self.keys))

    def testPressAndRelease(self):
        self.button.set_state(True)
        self.assertEvents(map(events.PressEvent, self.keys))


class TwoButtonAxisTest(InputUnitTest):

    THRESHOLD = 10
    POS_KEY = 20
    NEG_KEY = 35
    def setUp(self):
        super(TwoButtonAxisTest, self).setUp()
        self.button = inputs.TwoButtonAxis(self._eventFunc, self.THRESHOLD,
                                           self.POS_KEY,
                                           self.NEG_KEY)

    def testPress(self):
        self.button.set_state(5)
        self.assertEvents([])
        self.button.set_state(10) # Triggers at threshold
        self.assertEvents([events.PressEvent(self.POS_KEY)])
        self.button.set_state(15)
        self.assertEvents([])

    def testPressAndRelease(self):
        self.button.set_state(5)
        self.assertEvents([])
        self.button.set_state(10) # Triggers at threshold
        self.assertEvents([events.PressEvent(self.POS_KEY)])
        self.button.set_state(15)
        self.assertEvents([])
        self.button.set_state(10)
        self.assertEvents([])
        self.button.set_state(5)
        self.assertEvents([events.ReleaseEvent(self.POS_KEY)])

    def testPressAndReleaseNeg(self):
        self.button.set_state(-5)
        self.assertEvents([])
        self.button.set_state(-10) # Triggers at threshold
        self.assertEvents([events.PressEvent(self.NEG_KEY)])
        self.button.set_state(-15)
        self.assertEvents([])
        self.button.set_state(-10)
        self.assertEvents([])
        self.button.set_state(-5)
        self.assertEvents([events.ReleaseEvent(self.NEG_KEY)])

class MouseAxisTest(InputUnitTest):

    def setUp(self):
        self.AXIS = 'x'
        self.MAX = 100
        super(MouseAxisTest, self).setUp()
        self.button = inputs.MouseAxis(self._eventFunc, self.AXIS, self.MAX)

    def testWrap(self):
        self.button.set_state(3527) # Prime so wrapping won't hit max
        self.button.tick(0)
        event = self.getOnlyEvent()
        self.assertTrue(event.value < self.MAX)


    def testNoWrap(self):
        self.button = inputs.MouseAxis(
            self._eventFunc, self.AXIS, self.MAX, wrap=False)
        self.button.set_state(2) # Prime so wrapping won't hit max
        self.button.tick(0)
        event = self.getOnlyEvent()

        self.assertEqual(self.MAX, event.value)
        self.button.tick(10)
        event = self.getOnlyEvent()
        self.assertEqual(self.MAX, event.value)

    def testTick(self):
        previousValue = self.button.pos

        # Axis up
        self.button.set_state(self.button.threshold)
        self.button.tick(0)
        event = self.getOnlyEvent()
        self.assertEqual(self.AXIS, event.axis)
        self.assertTrue(event.value > 0)
        self.assertTrue(event.delta > 0)
        self.assertEqual(event.value, previousValue + event.delta)
        self.clearEvents()
        previousValue = event.value

        # Axis Up
        self.button.tick(10)
        event = self.getOnlyEvent()
        self.assertEqual(self.AXIS, event.axis)
        self.assertTrue(event.value > 0)
        self.assertTrue(event.delta > 0)
        self.assertEqual(event.value, previousValue + event.delta)
        self.assertTrue(event.value > previousValue)
        self.clearEvents()
        previousValue = event.value

        # Axis Zero
        self.button.set_state(0)
        self.button.tick(20)
        self.assertEvents([])

        # Axis Down
        self.button.set_state(-1 * self.button.threshold)
        self.button.tick(30)
        event = self.getOnlyEvent()
        self.assertEqual(self.AXIS, event.axis)
        self.assertTrue(event.value > 0)
        self.assertTrue(event.delta < 0)
        self.assertEqual(event.value, previousValue + event.delta)
        self.assertTrue(event.value < previousValue)
        self.clearEvents()

    def testNormalizedTheshold(self):
        self.assertEqual(self.button.normalized_state, 0)
        self.button.set_state(self.button.threshold)
        self.assertEqual(self.button.normalized_state, 1)
        self.button.set_state(2 * self.button.threshold)
        self.assertEqual(self.button.normalized_state, 2)
        self.button.set_state(0.5 * self.button.threshold)
        self.assertEqual(self.button.normalized_state, 0.0)

class MouseWheelButtonTest(InputUnitTest):
    def setUp(self):
        super(MouseWheelButtonTest, self).setUp()
        self.button = inputs.MouseWheelButton(self._eventFunc, 34)

    def testEvent(self):
        self.button.set_state(5)
        self.assertEvents([events.MouseWheelEvent(34)])

class KeySequenceButtonTest(InputUnitTest):
    def setUp(self):
        self.KEYS = [1, 2, 5, 10]
        super(KeySequenceButtonTest, self).setUp()
        self.button = inputs.KeySequenceButton(self._eventFunc, self.KEYS)

    def testEvent(self):
        def pressAndRelease(key):
            return (events.PressEvent(key), events.ReleaseEvent(key))

        self.button.set_state(True)
        evtList = [item for sublist in map(pressAndRelease, self.KEYS) for
                   item in sublist]
        self.assertEvents(evtList)

    def testNoEventOnRelease(self):
        self.button.set_state(False)
        self.assertEvents([])


if __name__ == "__main__":
    unittest.main()
