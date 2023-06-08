import asyncio
from collections.abc import AsyncGenerator, Awaitable
import os

from cytoolz.functoolz import curry

try:
  from .analyse_state_space import get_maude_tasks
except ImportError:
  @curry
  async def get_maude_tasks(
    natural4_file: str | os.PathLike,
    output_path: str | os.PathLike
  ) -> AsyncGenerator[Awaitable[None], None]:
    yield asyncio.to_thread(lambda: None)