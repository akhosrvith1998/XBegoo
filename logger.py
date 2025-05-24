import logging
import os

def setup_logger():
    logger = logging.getLogger('bot_logger')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('bot.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

logger = setup_logger()