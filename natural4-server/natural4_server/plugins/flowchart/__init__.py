import asyncio
from collections.abc import AsyncGenerator, Awaitable
import os

from cytoolz.functoolz import curry
from natural4_server.task import Task, no_op_task

try:
  from .flowchart_dot_to_outputs import get_flowchart_tasks
except ImportError:
  @curry
  async def get_flowchart_tasks(
    _uuid_ss_folder : str | os.PathLike,
    _timestamp : str | os.PathLike
  ) -> AsyncGenerator[Task, None]:
    yield no_op_task