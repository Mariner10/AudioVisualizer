import sys
import termios
import tty
import threading

class KeyboardHandler:
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _run(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            while self.running:
                char = sys.stdin.read(1)
                if char:
                    self.callback(char)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
