import logging

def setup_logger():
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    return logger
