import logging
from ws2811_mqtt.args import args_client

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(levelname)-5s:%(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def init_logger():
    log_client = logging.getLogger("ws2811-mqtt")
    log_client.handlers = []  # Clear existing handlers
    log_client.propagate = False
    verbosity_levels = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG
    }
    log_client.setLevel(verbosity_levels.get(args_client.verbosity, logging.INFO))

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(verbosity_levels.get(args_client.verbosity, logging.INFO))
    ch.setFormatter(CustomFormatter())
    log_client.addHandler(ch)
    return log_client

log_client = init_logger()