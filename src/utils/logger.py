import logging
import os
from datetime import datetime

def setup_logger(name="AudioVisualizer", level=logging.INFO):
    """Sets up a logger with console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding multiple handlers if setup_logger is called multiple times
    if logger.hasHandlers():
        return logger

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console Handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.log")
    fh = logging.FileHandler(log_file)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

# Global logger instance
logger = setup_logger()
