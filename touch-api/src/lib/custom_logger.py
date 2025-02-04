from uvicorn.config import LOGGING_CONFIG
import logging
logger = logging.getLogger('uvicorn.error')

LOGGING_CONFIG["formatters"]["default"]["datefmt"] = "%Y-%m-%d %H:%M:%S"
LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"