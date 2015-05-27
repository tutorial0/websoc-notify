import logging
import os.path
import time
import logging.handlers


now = str(int(time.time()))

def initialize_logger(output_dir):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
     
    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
 
    # create error file handler and set level to error
    handler = logging.handlers.TimedRotatingFileHandler(os.path.join(output_dir, "error.log"), encoding=None, delay="true", when='d')
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
 
    # create debug file handler and set level to debug
    handler = logging.handlers.TimedRotatingFileHandler(os.path.join(output_dir, "all.log"), encoding=None, delay="true", when='d')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
