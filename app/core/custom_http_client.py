import asyncio

import httpx


class CustomAsyncClient(httpx.AsyncClient):
    __slots__ = ("semaphore",)

    def __init__(self, *args, max_concurrency: int = 20, **kwargs):
        super().__init__(*args, **kwargs)
        self.semaphore = asyncio.Semaphore(max_concurrency)
