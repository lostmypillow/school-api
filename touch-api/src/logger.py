from rich.logging import RichHandler
from rich.traceback import install
import logging

install(show_locals=True)
rich_handler = RichHandler(rich_tracebacks=True)
logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[rich_handler]
)
for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
    logger = logging.getLogger(name)
    logger.handlers = [rich_handler]
    logger.setLevel(logging.INFO)

logger = logging.getLogger("rich")
