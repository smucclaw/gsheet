from collections.abc import AsyncGenerator
import os

from natural4_server.task import Task, no_op_task

try:
  from .flowchart_dot_to_outputs import get_flowchart_tasks
except ImportError:
  async def get_flowchart_tasks(
    uuid_ss_folder : str | os.PathLike,
    timestamp : str | os.PathLike
  ) -> AsyncGenerator[Task, None]:
    yield no_op_task