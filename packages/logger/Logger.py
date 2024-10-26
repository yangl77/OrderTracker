import logging
import os

class Logger:
    def __init__(self, logger_dir, log_level=logging.INFO):
        """Logger

        Args:
            logger_dir (str): absolute logger dir path
            log_level (_type_, optional): log level. Defaults to logging.INFO.
        """
        log_file = logger_dir + "/log/OrderTracker.log"

        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(log_level)
        
        # Formatter for log messages
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # File handler (logs to a file)
        if log_file:
            # Ensure log directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.__logger.addHandler(file_handler)

        # Console handler (logs to console)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.__logger.addHandler(console_handler)

    def info(self, message):
        self.__logger.info(message)

    def warning(self, message):
        self.__logger.warning(message)

    def error(self, message):
        self.__logger.error(message)

    def debug(self, message):
        self.__logger.debug(message)

    def critical(self, message):
        self.__logger.critical(message)


# if __name__ == '__main__':
#     log = Logger(log_level=logging.DEBUG)
    
#     log.info('This is an informational message.')
#     log.warning('This is a warning message.')
#     log.error('This is an error message.')
#     log.debug('This is a debug message.')
#     log.critical('This is a critical message.')