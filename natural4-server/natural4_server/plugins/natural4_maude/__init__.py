from collections.abc import AsyncGenerator
import os

from cytoolz.functoolz import curry
import pyrsistent as pyrs

from natural4_server.task import Task, no_op_task

try:
  from .analyse_state_space import get_maude_tasks
except ImportError:
  @curry
  async def get_maude_tasks(
    _natural4_file: str | os.PathLike,
    _output_path: str | os.PathLike
  ) -> AsyncGenerator[Task, None]:
    yield no_op_task