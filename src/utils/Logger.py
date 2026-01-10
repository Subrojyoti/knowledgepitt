import os
import sys
import logging
from functools import lru_cache
from src.utils.Singleton import Singleton
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

class CustomFormatter(logging.Formatter):
    def formatException(self, exec_info):
        result = super(CustomFormatter, self).formatException(exec_info)
        return result

    def format(self, record):
        message = record.msg
        lines = []
        for line in message.split('\n'):
            record.msg = line
            formatted_msg = super(CustomFormatter, self).format(record)
            lines.append(formatted_msg)
        
        s = "\n".join(lines)
        return s

class Logger(metaclass=Singleton):
    def __init__(self, log_file_name: str = None, log_path: str = None):
        if log_path and log_file_name:
            self.__log_file_path = os.path.join(log_path, log_file_name)
        self.__formatter = CustomFormatter("%(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)s "
                                            "%(message)s",
                                            '%Y-%m-%d %H:%M:%S')
        
    @lru_cache(maxsize=1024)
    def get_simple_logger(self, name="KnowledgePitt"):
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)

            # Ensure the logger's handlers are cleared
            logger.handlers.clear()

            #set up the stream handler to output stdout
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(self.__formatter)
            logger.addHandler(sh)

            return logger

    def create_size_rotating_log(self, name='rotating', max_bytes=104857600, backup_count=10) -> logging:
        path = self.__log_file_path
        logger = logging.getLoggger(f"{name} Log")
        logger.setLevel(logging.INFO)

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(self.__formatter)
        logger.handlers.clear()
        logger.addHandler(sh)

        # add a rotating handler
        handler = RotatingFileHandler(path, maxBytes=max_bytes, backupCount=backup_count)
        logger.addHandler(handler)
        handler.setFormatter(self.__formatter)
        
        return logger
    
    def create_time_rotating_log(self, name='rotating', when="minute", interval=1, backup_count=10) -> logging.Logger:
        valid_when_params = {"minute": "m", "second": "s", "hour": "h", "day": "d", "midnight": "MIDNIGHT"}
        when = valid_when_params.get(when.lower(), "m")
        if when is None:
            raise ValueError("Invalid when parameter")
        path = self.__log_file_path
        logger = logging.getLogger(f"{name} Log")
        logger.setLevel(logging.INFO)

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(self.__formatter)
        logger.handlers.clear()
        logger.addHandler(sh)

        # add a time rotating handler
        handler = TimedRotatingFileHandler(path, when=when, interval=interval, backupCount=backup_count)
        logger.addHandler(handler)
        handler.setFormatter(self.__formatter)
        

        
        