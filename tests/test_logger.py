import unittest
import os
import sys
import logging

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from utils.logger import setup_logger

class TestLogger(unittest.TestCase):
    def test_logger_setup(self):
        logger = setup_logger("TestLogger")
        self.assertEqual(logger.name, "TestLogger")
        self.assertTrue(logger.hasHandlers())
        
        # Check if log file is created
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        self.assertTrue(os.path.exists(log_dir))
        
    def test_singleton_behavior(self):
        from src.utils.logger import logger as logger1
        from src.utils.logger import logger as logger2
        self.assertIs(logger1, logger2)

if __name__ == '__main__':
    unittest.main()
