import asyncio
from collections.abc import AsyncGenerator, Callable, Sequence
import sys

from cytoolz.functoolz import curry
import pyrsistent as pyrs

from quart import Quart

class Task(pyrs.PRecord):
  func = pyrs.field(type = Callable, mandatory = True)
  args = pyrs.field(type = Sequence, initial = tuple()) 

no_op_task = Task(func = lambda: None)

async def run_tasks(
  tasks: AsyncGenerator[Task, None],
  timeout = 20
) -> None:
  '''
  Runs tasks asynchronously in the background.
  '''

  try:
    async with (
      asyncio.timeout(timeout),
      asyncio.TaskGroup() as taskgroup
    ):
      async for task in tasks:
        match task:
          case {'func': func, 'args': args}:
            print(f'Running task: {task}', file=sys.stderr)
            taskgroup.create_task(asyncio.to_thread(func, *args))

  except TimeoutError as exc:
    print(f'Timeout while generating outputs: {exc}', file=sys.stderr)

@curry
async def add_tasks_to_background(
  tasks: AsyncGenerator[Task, None],
  app: Quart
) -> None:
  async for task in tasks:
    match task:
      case {'func': func, 'args': args}:
        print(f'Adding background task: {task}', file=sys.stderr)
        app.add_background_task(func, *args)