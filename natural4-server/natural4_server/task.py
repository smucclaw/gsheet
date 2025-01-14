import asyncio
from collections.abc import AsyncGenerator, Callable, Coroutine, Generator, Sequence
import sys

import aiostream

import pyrsistent as pyrs


class Task(pyrs.PRecord):
    func = pyrs.field(type=Callable, mandatory=True)
    args = pyrs.field(type=Sequence, initial=tuple())
    name = pyrs.field(initial=None)


def _run_as_async(func: Callable, args: Sequence) -> Coroutine:
    if asyncio.iscoroutinefunction(func):
        return func(*args)
    else:
        return asyncio.to_thread(func, *args)


def task_to_coro(task: Task) -> Coroutine:
    match task:
        case {"func": func, "args": args}:
            return _run_as_async(func, args)
        # Dummy fall-through case just to silence the type checker.
        case _:
            return _run_as_async(lambda: None, tuple())


async def run_tasks(tasks: AsyncGenerator[Task, None] | Generator[Task, None, None]) -> None:
    """
    Runs tasks asynchronously in the background.
    """

    async with asyncio.TaskGroup() as taskgroup:
        async for task in aiostream.stream.iterate(tasks):
            print(f"Running task: {task}", file=sys.stderr)
            taskgroup.create_task(task_to_coro(task))


# @curry
# async def add_background_tasks(
#   tasks: AsyncGenerator[Task, None] | Generator[Task]
# ) -> None:
#   async for task in aiostream.stream.iterate(tasks):
#     print(f'Adding background task: {task}', file=sys.stderr)
#     asyncio.create_task(task_to_coro(task), name = task['name'])
