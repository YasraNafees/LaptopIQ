import logging
import sys 
from config import config

logging.getLogger("bm25s").setLevel(logging.WARNING) 
def setup_logger(name=__name__):
    """Sets up the logger for console and file."""
    logger=logging.getLogger(name)
    logger.setLevel(getattr(logging,config.LOG_LEVEL))
    # Check if handlers already exist to prevent duplicates
    if logger.handlers:
        return logger
    #Formatter
    formatter=logging.Formatter(
        '%(asctime)s-%(name)s-%(levelname)s-%(message)s',
         datefmt='%Y-%m-%d %H:%M:S' )
    #  Console handler (to display on terminal)
    try:
      

      file_handler=logging.FileHandler(config.LOG_FILE,mode='a')
      file_handler.setLevel(logging.DEBUG)
      file_handler.setFormatter(formatter)
      logger.addHandler(file_handler)

    except Exception as e:
       logger.error(f"log file does not create: {e}")

    
    return logger


# Global logger instance

logger=setup_logger()

print("suceesful")
