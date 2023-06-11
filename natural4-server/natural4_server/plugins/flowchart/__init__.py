import asyncio
from collections.abc import AsyncGenerator, Awaitable
import os

from cytoolz.functoolz import curry
import pyrsistent as pyrs

try:
  from .flowchart_dot_to_outputs import get_flowchart_tasks
except ImportError:
  @curry
  async def get_flowchart_tasks(
    _uuid_ss_folder : str | os.PathLike,
    _timestamp : str | os.PathLike
  ):
    # yield asyncio.to_thread(lambda: None)
    yield pyrs.m(
      func = lambda: None,
      args = tuple()
    )