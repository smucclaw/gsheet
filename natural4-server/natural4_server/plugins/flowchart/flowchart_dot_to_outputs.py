import asyncio
from collections.abc import AsyncGenerator, Collection, Sequence
import os
import pathlib
import sys

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

import pyrsistent as pyrs
import pyrsistent_extras as pyrse

import anyio

from natural4_server.task import Task

class FlowchartOutput(pyrs.PRecord):
  # petrifile{suffix}.{file_extension}
  suffix = pyrs.field(type = str, initial = '')
  file_extension = pyrs.field(mandatory = True, type = str)

  # We prefer PSequence, ie 2-3 finger tree, for args because the log(n) concat
  # makes it efficient to splice them with other stuff to construct commands
  # for subprocess.run.
  args = pyrs.field(type = Sequence, initial = pyrse.sq())

flowchart_outputs: Collection[FlowchartOutput] = pyrs.s(
  FlowchartOutput(
    file_extension = 'png',
    args = pyrse.sq('-Gdpi=150')
  ),
  FlowchartOutput(
    suffix = '-small',
    file_extension = 'png',
    args = pyrse.sq('-Gdpi=72')
  ),
  FlowchartOutput(
    file_extension = 'svg'
  )
)

# try:
# from pygraphviz import AGraph

# async def _dot_file_to_output(
#   dot_file: str | os.PathLike[str],
#   output_file: str | os.PathLike[str],
#   args: Sequence[str]
# ) -> None:
#   output_file = pathlib.Path(output_file) 
#   dot_file = pathlib.Path(dot_file)

#   args = ' '.join(args)
#   print(f'Graphviz args: {args}', file=sys.stderr)

#   await asyncio.to_thread(
#     AGraph(dot_file).draw,
#     output_file,
#     format = f'{output_file.suffix[1:]}',
#     prog = 'dot',
#     args = args
#   )

# except ImportError:
async def _dot_file_to_output(
  dot_file: str | os.PathLike[str],
  output_file: str | os.PathLike[str],
  args: Sequence[str]
) -> None:
  output_file = anyio.Path(output_file)

  graphviz_cmd: Sequence[str] = (
    pyrse.sq('dot', f'-T{output_file.suffix[1:]}', f'{dot_file}') +
    pyrse.psequence(args) +
    pyrse.sq('-o', f'{output_file}')
  ) # type: ignore

  print(f'Calling graphviz with: {" ".join(graphviz_cmd)}', file=sys.stderr)

  await asyncio.subprocess.create_subprocess_exec(
    *graphviz_cmd,
    stdout = asyncio.subprocess.PIPE, stderr = asyncio.subprocess.PIPE
  )

async def flowchart_dot_to_output(
  uuid_ss_folder: str | os.PathLike,
  timestamp: str | os.PathLike,
  flowchart_output: FlowchartOutput
) -> None:
  uuid_ss_folder_path = anyio.Path(uuid_ss_folder)
  output_path: anyio.Path = uuid_ss_folder_path / 'petri'
  await output_path.mkdir(parents=True, exist_ok=True)
  dot_file: anyio.Path = output_path / 'LATEST.dot'

  if await dot_file.exists():
    match flowchart_output:
      case {'suffix': suffix, 'file_extension': file_extension, 'args': args}:
        timestamp_file: str = f'{timestamp}{suffix}.{file_extension}'
        output_file: str = f'{output_path / timestamp_file}'

        print(f'Drawing {file_extension} from dot file', file=sys.stderr)
        print(f'Output file: {output_file}', file=sys.stderr)
        await _dot_file_to_output(dot_file, output_file, args)

        latest_file: anyio.Path = output_path / f'LATEST{suffix}.{file_extension}'
        try:
          await latest_file.unlink(missing_ok = True)
          await latest_file.symlink_to(timestamp_file)
          # os.symlink(timestamp_file, latest_file)
        except Exception as exc:
          print(
            'hello.py main: got some kind of OS error to do with the unlinking and the symlinking',
            file=sys.stderr
          )
          print(f'hello.py main: {exc}', file=sys.stderr)

async def get_flowchart_tasks(
  uuid_ss_folder: str | os.PathLike,
  timestamp: str | os.PathLike
) -> AsyncGenerator[Task, None]:
  for output in flowchart_outputs:
    yield Task(
      func = flowchart_dot_to_output,
      args = (uuid_ss_folder, timestamp, output)
    )