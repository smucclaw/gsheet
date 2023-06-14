from collections.abc import AsyncGenerator
import os

import aiostream

from natural4_server.task import Task

try:
  from .pandoc_md_to_outputs import get_pandoc_tasks
except ImportError:
  def get_pandoc_tasks(
    # markdown_coro: Awaitable[asyncio.subprocess.Process],
    uuid_ss_folder: str | os.PathLike,
    timestamp: str | os.PathLike
  ) -> AsyncGenerator[Task | None, None]:
    return aiostream.stream.empty()