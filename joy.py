#!/usr/bin/env python
import logging
logging.basicConfig(level=logging.DEBUG)
#hat1 = 10,11,12,13
hat1 = 10,11,12,13
logging.basicConfig()
log = logging.getLogger(__name__)
import sys
from subprocess import *
import time
import ConfigParser
from collections import defaultdict
import events

try:
    import pygame.joystick
    import pygame
except ImportError:
    print "Failed to import pygame, Press any key to quit."
    raw_input()
    sys.exit(-1)

from events import *
from inputs import *

class InputFilter(object):
    """Provides a filter layer so that key combos like down/down/up/up
    result in the key staying down until the last up"""
    def __init__(self, robot):
        self.robot = robot
        self.key_map = defaultdict(int)
    def send(self, event):
        if isinstance(event, events.PressEvent):
            self.key_map[event.key] += 1
            if self.key_map[event.key] != 1: # Only send event on first press
                return
        if isinstance(event, events.ReleaseEvent):
            self.key_map[event.key] -= 1
            if self.key_map[event.key] != 0: # Only send event on first press
                return
        self.robot.send(event)


class Controller(object):
    """Controller object. The ControllerFactory sets up all the binds.
    Inputs on the controller can register for a tick so that they can emit
    events on regular intervals to simulate mouse movement rather than only
    on button press / joystick movement.
    """
    def __init__(self, controller):
        self.controller = controller
        self.joy = pygame.joystick.Joystick(controller)
        self.joy.init()
        self.tick_listeners = []
        self.axis_map = {}
        self.hat_map = {}
        self.button_map = {}
        pass

    def add_tick_listener(self, _input):
        "Register an Input element to recieve tick events"
        self.tick_listeners.append(_input)

    def tick(self, i):
        "Run tick on all registered listeners so that they may emit events"
        for _input in self.tick_listeners:
            _input.tick(i)

    def button_press(self, button, state):
        try:
            self.button_map[button].set_state(state)
        except (AttributeError, KeyError):
            log.exception("Failed to register button press for button %d" % button )
        pass

    def hat_event(self, hat, value):
        buttons = self.hat_map[hat].update_state(value)
        for b,state in buttons:
            #log.warn((b,state))
            self.button_press(b,state)

    def axis_event(self, axis, value):
        try:
            self.axis_map[axis].set_state(value)
        except (AttributeError, KeyError):
            log.exception("Failed to register button press for axis %d" % axis )
        pass

class Config(ConfigParser.SafeConfigParser):
    "Extension of SafeConfigParser with some constants"
    CONTROLLER_SECTION_TEMPLATE = "Controller_%d"
    KEYMAP_SECTION = "keymap"
    BUTTON_MAP_SECTION = "buttonmap"
    AXIS_MAP_SECTION = "axismap"
    HAT_MAP_SECTION = "hatmap"
    MAIN_SECTION = "main"


class ControllerFactory(object):
    """Returns controllers built from a config.
    Abstracts out config and buttons from Controller.
    """

    def __init__(self, config, input_factory):
        self.config = config
        self.key_config = Config()
        self.key_config.read(config.get(Config.MAIN_SECTION, 'keymap_config'))
        self.defaults = {}
        #self._read_config(config)
        self.input_factory = input_factory


    def get_controller(self, i):
        """Returns a Controller for the specified player.
        If the section doesn't exist, raises an UnConfiguredControllerError"""
        section = Config.CONTROLLER_SECTION_TEMPLATE % i
        if not self.config.has_section(section):
            raise UnConfiguredControllerError(
                "No config found for controller %d" % i)

        controller = Controller(i)

        #Iterate through axis and button map sections, assigning all buttons

        controller.axis_map = self.setup_axes(section)
        for _input in controller.axis_map.values():
            if hasattr(_input, 'tick'):
                controller.add_tick_listener(_input)

        controller.button_map = self.setup_buttons(section)
        for _input in controller.button_map.values():
            if hasattr(_input, 'tick'):
                controller.add_tick_listener(_input)

        controller.hat_map = self.setup_hats(section)
        for _input in controller.hat_map.values():
            if hasattr(_input, 'tick'):
                controller.add_tick_listener(_input)

        return controller

    def setup_axes(self, section):
        """Returns a map of numeric input_id to an Input() object created
        based on the config."""
        input_id_map = self.get_input_id_map(Config.AXIS_MAP_SECTION)
        config_map = dict(self.config.items(section))
        input_map = self.build_input_map(
            self._create_axis, config_map, input_id_map)
        return input_map

    def setup_buttons(self, section):
        """Returns a map of numeric input_id to an Input() object created
        based on the config."""
        input_id_map = self.get_input_id_map(Config.BUTTON_MAP_SECTION)
        config_map = dict(self.config.items(section))
        input_map = self.build_input_map(
            self._create_button, config_map, input_id_map)
        return input_map

    def setup_hats(self, section):
        """Returns a map of numeric input_id to an Input() object created
        based on the config."""
        input_id_map = self.get_input_id_map(Config.HAT_MAP_SECTION)
        config_map = dict(self.config.items(section))
        input_map = self.build_input_map(
            self._create_hat, config_map, input_id_map)
        return input_map

    def get_input_id_map(self, section_name):
        """Returns a mapping of numeric input identifiers to text names.
        Returns: dict[int]string of the input id to a text name."""
        if not self.config.has_section(section_name):
            log.warn("No section %s in config, skipping" % section_name)
            return {}

        return dict([(int(id_), name) for (id_, name)
                     in self.config.items(section_name)
                     if id_ not in self.config.defaults()])

    def get_button_info(self, config_map, input_name):
        """Returns button config information for a given input_name.

        button_action is the primary value in the config file.
        button_metadata is a map created from all the input_name.%s values.

        Args:
        config_map -
        input_name -
        Returns: A tuple (button_action, button_metadata)
          button_metadata is a dict[str]str
          None if no value is found in the config.
        """
        button_action = config_map.get(input_name, None)
        if button_action is None:
            return None, None
        input_prefix = input_name + "."
        button_metadata = dict([(name.replace(input_prefix, ''), value)
                           for (name, value) in config_map.iteritems()
                           if name.startswith(input_prefix)])
        for (k, v) in button_metadata.iteritems():
            # Interpert false, no, and off as False
            if v.lower() in ('false', 'no', 'off'):
                button_metadata[k] = False
        return (button_action, button_metadata)

    def build_input_map(self, input_factory_func, config_map, input_id_map):
        """Reads a config section and returns it as a map[int]
        @param config_section_name
        """
        # Loop
        input_map = {}
        for (input_id, input_name) in input_id_map.iteritems():
            button_action, button_metadata = \
                self.get_button_info(config_map, input_name)
            if button_action is None: # Skip missing buttons
                # TODO(jfreidman): Maybe log
                continue

            _input = input_factory_func(button_action, button_metadata)
            if _input is None:
                continue #Don't have to map all keys

            input_map[int(input_id)] = _input
        return input_map



# TODO(jfreidman): Use reflection to pull extra config args for inputs
    def _create_axis(self, button_info, button_metadata):
        "Returns an axis-type input based on config params"
        if button_info in ('mouse-x', 'mouse-y'):
        #MouseAxis
            try:
                _max = int(button_metadata.get('max'))
                wrap = bool(button_metadata.get('wrap'))
                tick_mod = int(button_metadata.get('tick_mod', 1))
                axis = button_info.replace('mouse-','')
            except KeyError, msg:
                raise ConfigError(msg)
            log.info('zz')
            return self.input_factory.MouseAxis(
                axis, _max, wrap, tick_mod=tick_mod)
        else:
        #TwoButtonAxis
            try:
                neg_key, pos_key = map(self._get_keymap, button_info.split(' '))
            except ValueError:
                raise ConfigError("Bad value (%s) for config key %s in section %s" % (button_info, input_name, section))

            # TODO(jfreidman): Pull default from config
            threshold = float(button_metadata.get('threshold', 0.3))
            return self.input_factory.TwoButtonAxis(threshold, pos_key, neg_key)

    def _create_hat(self, button_info, button_metadata):
        buttons = button_info.split(",")
        if len(buttons) != 4:
            raise ConfigError("Need 4 buttons for hat")
        return self.input_factory.Hat(buttons)

    def _create_button(self, button_info, button_metadata):
        "Return a button-type input based on config params"
        #Each section can have different button types.
        #Someday this matching could be automated by a template in inputs so new input types are easier to add
        if button_info == 'wheelup':
        #MouseWheelButton
            return self.input_factory.MouseWheelButton(-1)
        elif button_info == 'wheeldown':
        #MouseWheelButton
            return self.input_factory.MouseWheelButton(1)
        if button_metadata.get('toggle', False):
            return self.input_factory.ToggleButton(
                self._get_keymap(button_info))
        if button_metadata.get('double_tap', False):
            return self.input_factory.DoubleTapButton(
                self._get_keymap(button_info))
        if button_info.find(",") > 0:
            return self.input_factory.MultiButton([self._get_keymap(p.strip()) for p in button_info.split(",")])
        if button_info.find(" ") > 0:
            return self.input_factory.MultiButton([self._get_keymap(p.strip()) for p in button_info.split(" ")])
        else:
        #StatefulButton
            return self.input_factory.StandardButton(self._get_keymap(button_info))

    def _get_keymap(self, key):
        """Return the Java InputEvent keybinding for a key
        Found at http://download-llnw.oracle.com/javase/6/docs/api/constant-values.html#java.awt.event.KeyEvent.VK_0
        This just reads out of the config file
        """
        if key is None or key.lower() == "none":
            return None
        try:
            return self.key_config.getint(Config.KEYMAP_SECTION, key)
        except ConfigParser.NoOptionError, msg:
            raise ConfigError(msg)


class Error(BaseException): pass
class NoJoyError(Error): pass
class ConfigError(Error):pass
class UnConfiguredControllerError(ConfigError):pass
class NoKeyError(ConfigError): pass

class Main(object):
    "Main event loop. Initializes the controllers then feeds input from pygame"
    def __init__(self, args):

        if len(args) < 2:
            self.config_name = 'joy.cfg'
            #print "Usage: %s [config_file]" % args[0]
            #sys.exit(-1)
        else:
            self.config_name = args[1]

        pygame.init()
        pygame.joystick.init()

        print 'zz'
        if not pygame.joystick.get_count():
            pass#raise NoJoyError("No joysticks found")
        self.config = self._parse_config(self.config_name)
        #self.robot = RobotInterface(self.config.get(Config.MAIN_SECTION, 'key_listener_app'))
        useWin32Relay = False
        try:
            import win32_relay
            print win32_relay
            useWin32Relay = True
        except ImportError:
            raise
            pass
        print "usewin", useWin32Relay
        if useWin32Relay:
            import win32_relay
            log.info("Using win32 relay")
            print 'using win32'
            self.robot = InputFilter(win32_relay.Win32Relay(''))
        else:
            self.robot = InputFilter(RobotInterface(self.config.get(Config.MAIN_SECTION, 'key_listener_app')))
        print self.robot
        self.controller_list = self._setup_controllers(self.config)

    def reload_config(self):
        try:
            pygame.joystick.init()
            config = self._parse_config(self.config_name)
            self.controller_list = self._setup_controllers(config)
        except BaseException:
            log.exception("Failed to load new config")
        else:
            self.config = config

    def _parse_config(self, config_name):
        pygame.display.init()
        defaults = dict(screen_x=str(pygame.display.Info().current_w),
                       screen_y=str(pygame.display.Info().current_h))
        config = Config(defaults)
        config.read(config_name)
        return config

    def _setup_controllers(self, config):
        input_factory = InputFactory(self.robot.send)
        controller_factory = ControllerFactory(config, input_factory)
        controller_list = []
        for i in xrange(pygame.joystick.get_count()):
            controller_list.append(controller_factory.get_controller(i))
        return controller_list

    def run(self):
        c = pygame.joystick.get_count()
        print 'Listening on %d joystick%s. Press Ctrl-C to restart.' % (c, '' if c==1 else 's')
        clock = pygame.time.Clock()

        running = True
        i = 0
        while running:
            clock.tick(60)
            i += 1
            i = i % 60
            for c in self.controller_list:
                c.tick(i)
            try:
                for e in pygame.event.get():
                    if e.dict.get('scancode',0) == 12:
                        running = False
                    log.debug(e)
                    if 'joy' not in e.dict:
                        continue
                    controller = self.controller_list[e.dict["joy"]]

                    if e.type == pygame.JOYHATMOTION:
                        #log.warn(e)
                        controller.hat_event(e.dict['hat'], e.dict['value'])
                    elif e.type == pygame.JOYBUTTONDOWN:
                        try:
                            controller.button_press(e.dict['button'], True)
                        except KeyError:
                            pass
                    elif e.type == pygame.JOYBUTTONUP:
                        try:
                            controller.button_press(e.dict['button'], False)
                        except KeyError:
                            pass
                    elif e.type == pygame.JOYAXISMOTION:
                        controller.axis_event(e.dict['axis'], e.dict['value'])
            except:
                log.exception("Failed to handler %s event (%s)" % (e.type, e))


if __name__ == "__main__":
    try:
        import traceback
        m = Main(sys.argv)
        while True:
            try:
                m.run()
            except KeyboardInterrupt:
                print 'Reloading config in 2s, press Ctrl-C again to quit'
                time.sleep(2)
                m.reload_config()
    except BaseException, e:
        traceback.print_exc()
        print e
        raw_input()
