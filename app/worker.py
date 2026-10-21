import logging
from os import getenv

from dotenv import load_dotenv
from redis import Redis
from rq import Queue, Worker


load_dotenv()
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


def run_worker():
    conn: Redis = Redis.from_url(f"redis://{getenv("REDIS_HOST", "localhost")}:6379/0")
    queues = [Queue(name="default", connection=conn)]
    worker = Worker(queues, connection=conn)
    logger.info("Starting standard RQ worker listening on 'default' queue...")
    worker.work()


if __name__ == "__main__":
    run_worker()
