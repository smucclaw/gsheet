from collections.abc import AsyncGenerator
import os

import aiostream

from natural4_server.task import Task

try:
    from .analyse_state_space import get_maude_tasks
except ImportError:
    def get_maude_tasks(
            natural4_file: str | os.PathLike,
            output_path: str | os.PathLike
    ) -> AsyncGenerator[Task | None, None]:
        return aiostream.stream.empty()
