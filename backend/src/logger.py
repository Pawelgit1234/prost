import logging
import sys

FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format=FORMAT,
        datefmt=DATEFMT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )