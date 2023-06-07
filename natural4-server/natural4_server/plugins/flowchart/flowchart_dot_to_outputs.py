import asyncio
import os
import subprocess
import sys
from pathlib import Path

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

import pyrsistent as pyrs
import pyrsistent.typing as pyrst

try:
  from pygraphviz import AGraph

  @curry
  def _dot_file_to_output(
    dot_file: str | os.PathLike,
    output_file: str | os.PathLike,
    args: str
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
    args: str
  ) -> None:
    # WARNING: Potentially unsafe.
    subprocess.run(
      ['dot', f'{dot_file}', f'{args}', '-o', f'{output_file}'],
      stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

class FlowchartOutput(pyrs.PRecord):
  # petrifile{suffix}.{file_extension}
  suffix = pyrs.field(type = str, initial = '')
  file_extension = pyrs.field(mandatory = True, type = str)
  args = pyrs.field(type = str, initial = '')

flowchart_outputs:pyrst.PSet[FlowchartOutput] = pyrs.s(
  FlowchartOutput(
    file_extension = 'png',
    args = '-Gdpi=150'
  ),
  FlowchartOutput(
    suffix = '-small',
    file_extension = 'png',
    args = '-Gdpi=72'
  ),
  FlowchartOutput(
    file_extension = 'svg'
  )
)

@curry
def flowchart_dot_to_output(
  uuid_ss_folder: str | os.PathLike,
  timestamp: str,
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
        _dot_file_to_output(dot_file, output_file, args)

        latest_file = output_path / f'LATEST{suffix}.{file_extension}'
        try:
          if latest_file.exists():
            latest_file.unlink()
          latest_file.symlink_to(timestamp_file)
          # os.symlink(timestamp_file, latest_file)
        except Exception as e:
          print(
            'hello.py main: got some kind of OS error to do with the unlinking and the symlinking',
            file=sys.stderr
          )
          print(f'hello.py main: {e}', file=sys.stderr)

@curry
async def flowchart_dot_to_outputs(
  uuid_ss_folder: str | os.PathLike,
  timestamp: str
) -> None:
  try:
    async with (asyncio.timeout(15), asyncio.TaskGroup() as tasks):
      for flowchart_output in flowchart_outputs:
        pipe(
          (flowchart_dot_to_output, uuid_ss_folder, timestamp, flowchart_output),
          lambda x: asyncio.to_thread(*x),
          tasks.create_task
        )
  except TimeoutError:
    print("Pandoc timeout", file=sys.stderr)

@curry
def run_flowchart_dot_to_outputs(
  uuid_ss_folder: str | os.PathLike,
  timestamp: str
) -> None:
  asyncio.run(flowchart_dot_to_outputs(uuid_ss_folder, timestamp))