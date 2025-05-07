from uvicorn.config import LOGGING_CONFIG
import logging
logger = logging.getLogger('uvicorn.error')
LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(levelprefix)s %(message)s"