import asyncio
from collections.abc import AsyncGenerator, Callable, Generator, Sequence
import sys

from sanic import Sanic

import aiostream

from cytoolz.functoolz import curry
import pyrsistent as pyrs

class Task(pyrs.PRecord):
  func = pyrs.field(type = Callable, mandatory = True)
  args = pyrs.field(type = Sequence, initial = tuple()) 
  name = pyrs.field(initial = None)
  delay = pyrs.field(type = int, initial = 10)

no_op_task = Task(func = lambda: None)

# @curry
# def _ensure_async(func, args):
#   if asyncio.iscoroutinefunction(func):
#     return func(*args)
#   else:
#     return asyncio.to_thread(func, *args)

async def task_to_coro(task: Task):
  match task:
    case {'func': func, 'args': args, 'delay': delay}:
      try:
        async with asyncio.timeout(delay):
          if asyncio.iscoroutinefunction(func):
            await func(*args)
          else:
            await asyncio.to_thread(func, *args)
      except TimeoutError:
        print(f'Timeout in task: {task}', file=sys.stderr)

async def run_tasks(
  tasks: AsyncGenerator[Task, None] | Generator[Task]
) -> None:
  '''
  Runs tasks asynchronously in the background.
  '''

  async with asyncio.TaskGroup() as taskgroup:
    async for task in aiostream.stream.iterate(tasks):
      print(f'Running task: {task}', file=sys.stderr)
      taskgroup.create_task(task_to_coro(task))

@curry
async def add_tasks_to_background(
  app: Sanic,
  tasks: AsyncGenerator[Task, None] | Generator[Task]
) -> None:
  async for task in aiostream.stream.iterate(tasks):
    print(f'Adding background task: {task}', file=sys.stderr)
    app.add_task(task_to_coro(task), name = task['name'])