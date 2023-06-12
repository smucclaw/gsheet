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

no_op_task = Task(func = lambda: None)

async def run_tasks(
  tasks: AsyncGenerator[Task, None] | Generator[Task],
  delay = 10
) -> None:
  '''
  Runs tasks asynchronously in the background.
  '''

  try:
    async with (
      asyncio.timeout(delay),
      asyncio.TaskGroup() as taskgroup
    ):
      async for task in aiostream.stream.iterate(tasks):
        match task:
          case {'func': func, 'args': args}:
            print(f'Running task: {task}', file=sys.stderr)
            if asyncio.iscoroutinefunction(func):
              task = func(*args)
            else:
              task = asyncio.to_thread(func, *args)
            taskgroup.create_task(task)

  except TimeoutError as exc:
    print(f'Timeout while generating outputs: {exc}', file=sys.stderr)

@curry
async def add_tasks_to_background(
  tasks: AsyncGenerator[Task, None],
  app: Sanic
) -> None:
  async for task in tasks:
    match task:
      case {'func': func, 'args': args}:
        print(f'Adding background task: {task}', file=sys.stderr)
        if asyncio.iscoroutinefunction(func):
          task = func(*args)
        else:
          task = asyncio.to_thread(func, *args)
        app.add_task(task)
        # app.add_background_task(func, *args)