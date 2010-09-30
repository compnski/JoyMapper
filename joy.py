#!/usr/bin/env python2.6
import logging
logging.basicConfig()
log = logging.getLogger(__name__)

import sys
from subprocess import *
import time
import ConfigParser

import pygame.joystick
import pygame

from events import *
from inputs import *

class RobotInterface(object):

    def __init__(self, bot_cmd):
        self.bot_cmd = bot_cmd.split(" ")
        self.relaybot = self._spawn_relaybot()

    def _spawn_relaybot(self):
        return Popen(self.bot_cmd, stdin=PIPE, stdout=sys.stdout)

    def send(self, data):
        if self.relaybot.poll() is not None:
            log.error("RelayBot quit with error code %d" % self.relaybot.returncode)
            self.relaybot = self._spawn_relaybot
        print >>self.relaybot.stdin, data

class Controller(object):
    def __init__(self, controller):
        self.controller = controller
        self.joy = pygame.joystick.Joystick(controller)
        self.joy.init()
        self.tick_listeners = []
        self.axis_map = {}
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

    def axis_event(self, axis, value):
        try:
            self.axis_map[axis].set_state(value)
        except (AttributeError, KeyError):
            log.exception("Failed to register button press for axis %d" % axis )
        pass

class Config(ConfigParser.SafeConfigParser):
    CONTROLLER_SECTION_TEMPLATE = "Controller_%d"
    KEYMAP_SECTION = "keymap"
    BUTTON_MAP_SECTION = "buttonmap"
    AXIS_MAP_SECTION = "axismap"
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
        "Returns a Controller for the specified player. If the section doesn't exist, raises an UnConfiguredControllerError"
        section = Config.CONTROLLER_SECTION_TEMPLATE % i
        if not self.config.has_section(section):
            raise UnConfiguredControllerError("No config found for controller %d" % i)

        controller = Controller(i)

        #Iterate through axis and button map sections, assigning all buttons
        for datasection, array in ((Config.BUTTON_MAP_SECTION, controller.button_map), (Config.AXIS_MAP_SECTION, controller.axis_map)):
            print datasection
            for num in self.config.options(datasection):
                if num in self.config.defaults():
                    continue #hack around defaults adding themselves to each section
                try:
                    print num
                    input_name = self.config.get(datasection, num)
                    _input = self._get_button(section, input_name)
                    array[int(num)] = _input
                    if hasattr(_input, 'tick'):
                        controller.add_tick_listener(_input)
                except ConfigParser.NoOptionError:
                    log.warn("No button defined for %d=%s" % (num, input_name))

        return controller

    def _get_button(self, section, input_name):
        button_info = self.config.get(section, input_name)
        if button_info.find(' ') != -1:
            #TwoButtonAxis
            try:
                neg_key, pos_key = map(self._get_keymap, button_info.split(' '))
            except ValueError:
                raise ConfigError("Bad value (%s) for config key %s in section %s" % (button_info, input_name, section))
            if self.config.has_option(section, '%s.threshold' % input_name):
                threshold = self.config.getfloat(section, '%s.threshold' % input_name)
            else: #default is in axis.threshold
                threshold = self.config.getfloat(section, 'axis.threshold')
            return self.input_factory.TwoButtonAxis(threshold, pos_key, neg_key)

        elif button_info in ('mouse-x', 'mouse-y'):
            #MouseAxis
            try:
                _max = self.config.getint(section, '%s.max' % input_name)
                wrap = self.config.getboolean(section, '%s.wrap' % input_name)
            except ConfigParser.NoOptionError, msg:
                raise ConfigError(msg)
            return self.input_factory.MouseAxis(button_info.replace('mouse-',''),
                                                _max,
                                                wrap)
        elif button_info == 'wheelup':
            #MouseWheelButton
            return self.input_factory.MouseWheelButton(-1)

        elif button_info == 'wheeldown':
            #MouseWheelButton
            return self.input_factory.MouseWheelButton(1)

        else:
            #StatefulButton
            return self.input_factory.StatefulButton(self._get_keymap(button_info))

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

    def __init__(self, args):

        if len(args) < 2:
            print "Usage: %s [config_file]" % args[0]
            sys.exit(-1)

        pygame.init()
        pygame.joystick.init()

        if not pygame.joystick.get_count():
            raise NoJoyError("No joysticks found")

        self.config = self._parse_config(args[1])
        self.robot = RobotInterface(self.config.get(Config.MAIN_SECTION, 'key_listener_app'))

        self.controller_list = self._setup_controllers(self.config)


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
        clock = pygame.time.Clock()

        running = True
        i = 0
        while running:
            clock.tick(60)
            i += 1
            i = i % 60
            for c in self.controller_list:
                c.tick(i)
            for e in pygame.event.get():
                if e.dict.get('scancode',0) == 12:
                    running = False
                print >>sys.stderr,e
                if 'joy' not in e.dict:
                    continue
                controller = self.controller_list[e.dict["joy"]]

                if e.type == pygame.JOYHATMOTION:
                    controller.axis_event(e.dict['axis'], e.dict['value'])
                elif e.type == pygame.JOYBUTTONDOWN:
                    try:
                        controller.button_press(e.dict['button'], True)
                    except KeyError:
                        pass
                        #print >>sys.stderr, e
                elif e.type == pygame.JOYBUTTONUP:
                    try:
                        controller.button_press(e.dict['button'], False)
                    except KeyError:
                        pass
                elif e.type == pygame.JOYAXISMOTION:
                    controller.axis_event(e.dict['axis'], e.dict['value'])




if __name__ == "__main__":
    Main(sys.argv).run()
