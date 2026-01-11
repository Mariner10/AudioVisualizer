import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.state import StateMachine, AppState, PlaybackState, RecordingState

class TestStateMachine(unittest.TestCase):
    def setUp(self):
        self.sm = StateMachine()

    def test_initial_state(self):
        self.assertEqual(self.sm.app_state, AppState.IDLE)
        self.assertEqual(self.sm.playback_state, PlaybackState.STOPPED)
        self.assertEqual(self.sm.recording_state, RecordingState.IDLE)

    def test_state_transitions(self):
        self.sm.set_app_state(AppState.RUNNING)
        self.assertEqual(self.sm.app_state, AppState.RUNNING)
        
        self.sm.set_playback_state(PlaybackState.PLAYING)
        self.assertEqual(self.sm.playback_state, PlaybackState.PLAYING)
        
        self.sm.set_recording_state(RecordingState.RECORDING)
        self.assertEqual(self.sm.recording_state, RecordingState.RECORDING)

    def test_callbacks(self):
        called = []
        def callback(sm):
            called.append(sm.app_state)
            
        self.sm.register_callback(callback)
        self.sm.set_app_state(AppState.STARTING)
        
        self.assertIn(AppState.STARTING, called)

    def test_error_state(self):
        self.sm.set_error("Test Error")
        self.assertEqual(self.sm.app_state, AppState.ERROR)

if __name__ == '__main__':
    unittest.main()
