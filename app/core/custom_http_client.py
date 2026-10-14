from asyncio import Semaphore

from httpx import AsyncClient


class CustomAsyncClient(AsyncClient):
    __slots__ = ("semaphore",)

    def __init__(self, *args, max_concurrency: int = 20, **kwargs):
        super().__init__(*args, **kwargs)
        self.semaphore: Semaphore = Semaphore(max_concurrency)
