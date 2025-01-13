from collections.abc import AsyncGenerator
import os
import subprocess

import aiostream

from natural4_server.task import Task

from .flowchart_dot_to_outputs import get_flowchart_tasks as _get_flowchart_tasks

if subprocess.check_output("which dot", shell=True).strip():
    get_flowchart_tasks = _get_flowchart_tasks
else:
    def get_flowchart_tasks(
        uuid_ss_folder: str | os.PathLike, timestamp: str | os.PathLike
    ) -> AsyncGenerator[Task | None, None]:
        return aiostream.stream.empty()
