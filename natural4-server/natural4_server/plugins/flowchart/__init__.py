from collections.abc import AsyncGenerator
import os
import subprocess

from natural4_server.task import Task, no_op_task

from .flowchart_dot_to_outputs import get_flowchart_tasks as _get_flowchart_tasks

if subprocess.check_output('which dot', shell=True).strip(): 
  get_flowchart_tasks = _get_flowchart_tasks
else:
  async def get_flowchart_tasks(
    uuid_ss_folder : str | os.PathLike,
    timestamp : str | os.PathLike
  ) -> AsyncGenerator[Task, None]:
    yield no_op_task