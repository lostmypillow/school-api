from itertools import cycle
from typing import Iterable

def create_cycler(iterable: Iterable):
    cycler = cycle(iterable)

    def next_video():
        return next(cycler)
    return next_video
