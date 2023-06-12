import asyncio
from collections.abc import AsyncGenerator, Callable, Sequence
import inspect
import sys

from cytoolz.functoolz import curry
import pyrsistent as pyrs

# from quart import Quart
import muffin

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
  app: muffin.Application
) -> None:
  async for task in tasks:
    match task:
      case {'func': func, 'args': args}:
        print(f'Adding background task: {task}', file=sys.stderr)
        if inspect.iscoroutinefunction(func):
          print(f'is coroutine func: {func}', file=sys.stderr)
          task = func(*args)
        else:
          task = asyncio.to_thread(func, *args)

        asyncio.get_event_loop().create_task(task)
        # app.run_after_response(task())

        # app.add_background_task(func, *args)