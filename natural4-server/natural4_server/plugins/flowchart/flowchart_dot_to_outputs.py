import asyncio
from collections.abc import AsyncGenerator, Awaitable, Collection, Sequence
import os
from pathlib import Path
import subprocess
import sys

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

import pyrsistent as pyrs
import pyrsistent_extras as pyrse

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

try:
  from pygraphviz import AGraph

  @curry
  def _dot_file_to_output(
    dot_file: str | os.PathLike,
    output_file: str | os.PathLike,
    args: Sequence[str]
  ) -> None:
    pipe(
      dot_file,
      AGraph,
      do(lambda graph: graph._draw(output_file, args = args))
    )

except ImportError:
  @curry
  def _dot_file_to_output(
    dot_file: str | os.PathLike,
    output_file: str | os.PathLike,
    args: Sequence[str]
  ) -> None:
    graphviz_cmd = (
      pyrse.sq('dot', f'-T{Path(output_file).suffix[1:]}', f'{dot_file}') +
      args +
      pyrse.sq('-o', f'{output_file}')
    )
    print(f'Calling graphviz with: {" ".join(graphviz_cmd)}', file=sys.stderr)

    subprocess.run(
      # Log(n) concat go brr
      graphviz_cmd,
      stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

@curry
def flowchart_dot_to_output(
  uuid_ss_folder: str | os.PathLike,
  timestamp: str | os.PathLike,
  flowchart_output: FlowchartOutput
) -> None:
  uuid_ss_folder_path = Path(uuid_ss_folder)
  output_path = uuid_ss_folder_path / 'petri'
  output_path.mkdir(parents=True, exist_ok=True)
  dot_file = output_path / 'LATEST.dot'

  if dot_file.exists():
    match flowchart_output:
      case {'suffix': suffix, 'file_extension': file_extension, 'args': args}:
        timestamp_file = f'{timestamp}{suffix}.{file_extension}'
        output_file = f'{output_path / timestamp_file}'

        print(f'Drawing {file_extension} from dot file', file=sys.stderr)
        print(f'Output file: {output_file}', file=sys.stderr)
        _dot_file_to_output(dot_file, output_file, args)

        latest_file = output_path / f'LATEST{suffix}.{file_extension}'
        try:
          latest_file.unlink(missing_ok = True)
          latest_file.symlink_to(timestamp_file)
          # os.symlink(timestamp_file, latest_file)
        except Exception as e:
          print(
            'hello.py main: got some kind of OS error to do with the unlinking and the symlinking',
            file=sys.stderr
          )
          print(f'hello.py main: {e}', file=sys.stderr)

@curry
async def get_flowchart_tasks(
  uuid_ss_folder: str | os.PathLike,
  timestamp: str
) -> AsyncGenerator[Awaitable[None], None]:
  for output in flowchart_outputs:
    yield asyncio.to_thread(
      flowchart_dot_to_output, uuid_ss_folder, timestamp, output
    )
  # return (flowchart_outputs
  #   | stream.iterate
  #   | pipe.map(partial(
  #       asyncio.to_thread, flowchart_dot_to_output, uuid_ss_folder, timestamp
  #     ))
  # )

  # try:
  #   async with (asyncio.timeout(15), asyncio.TaskGroup() as tasks):
  #     for flowchart_output in flowchart_outputs:
  #       pipe(
  #         (flowchart_dot_to_output, uuid_ss_folder, timestamp, flowchart_output),
  #         lambda x: asyncio.to_thread(*x),
  #         tasks.create_task
  #       )
  # except TimeoutError:
  #   print("Flowchart graphviz timeout", file=sys.stderr)

# @curry
# def run_flowchart_dot_to_outputs(
#   uuid_ss_folder: str | os.PathLike,
#   timestamp: str
# ) -> None:
#   asyncio.run(flowchart_dot_to_outputs(uuid_ss_folder, timestamp))