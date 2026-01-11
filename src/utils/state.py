from enum import Enum, auto
from utils.logger import logger

class AppState(Enum):
    IDLE = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    ERROR = auto()

class PlaybackState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()

class RecordingState(Enum):
    IDLE = auto()
    RECORDING = auto()

class StateMachine:
    def __init__(self):
        self._app_state = AppState.IDLE
        self._playback_state = PlaybackState.STOPPED
        self._recording_state = RecordingState.IDLE
        self._error_message = ""
        self._callbacks = []

    @property
    def app_state(self):
        return self._app_state

    @property
    def playback_state(self):
        return self._playback_state

    @property
    def recording_state(self):
        return self._recording_state

    def register_callback(self, callback):
        self._callbacks.append(callback)

    def _notify(self):
        for cb in self._callbacks:
            try:
                cb(self)
            except Exception as e:
                logger.error(f"Error in state machine callback: {e}")

    def set_app_state(self, state: AppState):
        if self._app_state != state:
            logger.info(f"App state transition: {self._app_state.name} -> {state.name}")
            self._app_state = state
            self._notify()

    def set_playback_state(self, state: PlaybackState):
        if self._playback_state != state:
            logger.info(f"Playback state transition: {self._playback_state.name} -> {state.name}")
            self._playback_state = state
            self._notify()

    def set_recording_state(self, state: RecordingState):
        if self._recording_state != state:
            logger.info(f"Recording state transition: {self._recording_state.name} -> {state.name}")
            self._recording_state = state
            self._notify()

    def set_error(self, message: str):
        self._error_message = message
        logger.error(f"App error: {message}")
        self.set_app_state(AppState.ERROR)
