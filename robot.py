import subprocess
import logging
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig()
log = logging.getLogger(__name__)

class RobotInterface(object):
    """Interface to RelayBot. Checks that it is running, restarts if it dies.
    Sends commands over a pipe to stdin"""
    def __init__(self, bot_cmd):
        self.bot_cmd = bot_cmd.split(" ")
        self.relaybot = self._spawn_relaybot()

    def _spawn_relaybot(self):
        return subprocess.Popen(self.bot_cmd, stdin=PIPE, stdout=sys.stdout)

    def send(self, data):
        if self.relaybot.poll() is not None:
            log.error("RelayBot quit with error code %d" %
                      self.relaybot.returncode)
            self.relaybot = self._spawn_relaybot()
        print >>self.relaybot.stdin, data
