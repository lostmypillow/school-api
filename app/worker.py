import logging
import os

from dotenv import load_dotenv
from redis import Redis
from rq import Queue, Worker

load_dotenv()
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


def run_worker():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    conn = Redis.from_url(redis_url)
    queues = [Queue("default", connection=conn)]
    worker = Worker(queues, connection=conn)
    logger.info("Starting standard RQ worker listening on 'default' queue...")
    worker.work()


if __name__ == "__main__":
    run_worker()
