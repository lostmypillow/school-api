import asyncio
import logging

from app.domains.courses.tasks.bootstrap_mssql import bootstrap_mssql
from app.domains.courses.tasks.scrape import scrape_to_parquet

logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)


def _cleanup_child_resources() -> None:
    """Unregisters parent-inherited semaphores from the multiprocessing resource_tracker daemon."""
    try:
        from multiprocessing import resource_tracker
        if hasattr(resource_tracker, "_resource_tracker") and hasattr(resource_tracker._resource_tracker, "_registry"):
            for rtype in ("semaphore", "shared_memory"):
                for name in list(resource_tracker._resource_tracker._registry.get(rtype, set())):
                    try:
                        resource_tracker.unregister(name, rtype)
                    except Exception:
                        pass
    except Exception:
        pass


def scrape_to_parquet_task() -> None:
    """Standard synchronous RQ task entrypoint for scraping NTUT catalog to Parquet."""
    try:
        return asyncio.run(scrape_to_parquet())
    finally:
        _cleanup_child_resources()


def bootstrap_mssql_task() -> dict[str, int]:
    """Standard synchronous RQ task entrypoint for bootstrapping MSSQL from Parquet."""
    try:

        return asyncio.run(bootstrap_mssql())
    finally:
        _cleanup_child_resources()
