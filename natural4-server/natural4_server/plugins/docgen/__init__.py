import asyncio
from collections.abc import AsyncGenerator, Awaitable
import os

from cytoolz.functoolz import curry

try:
  from .pandoc_md_to_outputs import get_pandoc_tasks
except ImportError:
  @curry
  async def get_pandoc_tasks(
    markdown_coro: Awaitable[asyncio.subprocess.Process],
    uuid_ss_folder: str | os.PathLike,
    timestamp: str
  ) -> AsyncGenerator[Awaitable[None], None, None]:
    return