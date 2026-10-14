# main.py
import logging
import platform
if platform.system() == "Linux":
    pass
from fastapi import APIRouter
from app.domains.ldap.routers.ldap_router import router as ldap_router
from app.domains.ldap.services.ldap_service import LdapService


logger = logging.getLogger(__name__)


async def scheduled_ldap_sync() -> None:
    """Job that runs every day at 7pm."""
    ldap_service = LdapService()
    await ldap_service.sync_all_users()


# async def lifespan(app: FastAPI):  # noqa: ANN201
#     # Only attempt lock if not in DEV mode
#     if os.getenv("DEV") != "true" and platform.system() == "Linux":
#         # Keep the file handle alive to maintain the lock
#         app.state.lock_file = await aiofiles.open("scheduler.lock", "wb")
#         try:
#             # LOCK_EX: Exclusive lock, LOCK_NB: Non-blocking
#             fcntl.flock(app.state.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
# 
#             # This block only runs in the worker that gets the lock
#             app.state.scheduler = AsyncIOScheduler()
#             app.state.scheduler.add_job(scheduled_ldap_sync, "cron", hour=19, minute=0)
#             app.state.scheduler.start()
#             logger.info("Scheduler started successfully in this worker.")
# 
#         except BlockingIOError:
#             logger.info("Another worker is already running the scheduler.")
#             app.state.scheduler = None
#     else:
#         logger.info("Development mode: scheduler skipped.")
#     yield
#     if async_engine:
#         logger.debug("async_engine is valid, awaiting disposal")
#         await async_engine.dispose()
#         logger.debug("async engine disposed")
#     logger.info("internal-api shutdown complete.")


router = APIRouter(prefix="/ldap")



router.include_router(ldap_router)

