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

no_op_task = Task(func = lambda: None)

def run_as_async(func, args):
  if asyncio.iscoroutinefunction(func):
    return func(*args)
  else:
    return asyncio.to_thread(func, *args)

def task_to_coro(task: Task):
  match task:
    case {'func': func, 'args': args}:
      return run_as_async(func, args)

async def run_tasks(
  tasks: AsyncGenerator[Task, None] | Generator[Task, None, None]
) -> None:
  '''
  Runs tasks asynchronously in the background.
  '''

  async with asyncio.TaskGroup() as taskgroup:
    async for task in aiostream.stream.iterate(tasks):
      print(f'Running task: {task}', file=sys.stderr)
      taskgroup.create_task(task_to_coro(task))

@curry
async def add_background_tasks(
  tasks: AsyncGenerator[Task, None] | Generator[Task]
) -> None:
  async for task in aiostream.stream.iterate(tasks):
    print(f'Adding background task: {task}', file=sys.stderr)
    asyncio.create_task(task_to_coro(task), name = task['name'])