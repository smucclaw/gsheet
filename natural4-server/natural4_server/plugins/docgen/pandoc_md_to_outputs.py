from collections.abc import AsyncGenerator, Collection, Sequence
import os
import sys
from pathlib import Path

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

import pyrsistent as pyrs

import pypandoc

from natural4_server.task import Task

class PandocOutput(pyrs.PRecord):
  file_extension = pyrs.field(mandatory = True, type = str)
  extra_args = pyrs.field(
    Sequence, initial = ()
  )

pandoc_outputs: Collection[PandocOutput] = pyrs.s(
  PandocOutput(
    file_extension = 'docx',
    extra_args = (
      '-f', 'markdown+hard_line_breaks',
      '-s'
    )
  ),
  PandocOutput(
    file_extension = 'pdf',
    extra_args = (
      '--pdf-engine=xelatex',
      '-V', 'CJKmainfont=Droid Sans Fallback',
      '-f', 'markdown+hard_line_breaks',
      '-s'
    )
  )
)

def pandoc_md_to_output(
  uuid_ss_folder: str | os.PathLike,
  timestamp: str | os.PathLike,
  pandoc_output: PandocOutput
) -> None:
  uuid_ss_folder_path = Path(uuid_ss_folder)
  md_file: Path = uuid_ss_folder_path / 'md' / 'LATEST.md' # f'{timestamp}.md'
  # pipe(
  #   uuid_ss_folder_path / 'md',
  #   do(lambda x: x.mkdir(parents=True, exist_ok=True)),
  #   lambda x: x / f'{timestamp}.md'
  if md_file.exists():
    match pandoc_output:
      case {'file_extension': file_extension, 'extra_args': extra_args}:
        outputpath:Path = uuid_ss_folder_path / file_extension
        outputpath.mkdir(parents=True, exist_ok=True)

        timestamp_file: str = f'{timestamp}.{file_extension}'
        outputfile: str = f'{outputpath / timestamp_file}'

        print(f'Outputting to {file_extension}', file=sys.stderr)
        try:
          pypandoc.convert_file(
            md_file, file_extension,
            outputfile = outputfile, extra_args = extra_args 
          )
        except RuntimeError as exc:
          print(
            f'Error occured while outputting to {file_extension}: {exc}',
            file=sys.stderr
          )

        latest_file: Path = outputpath / f'LATEST.{file_extension}'
        latest_file.unlink(missing_ok = True)
        latest_file.symlink_to(timestamp_file)
      case _ : pass

async def get_pandoc_tasks(
  # markdown_coro: Awaitable[asyncio.subprocess.Process],
  uuid_ss_folder: str | os.PathLike,
  timestamp: str | os.PathLike,
) -> AsyncGenerator[Task, None]:
  # markdown_proc: asyncio.subprocess.Process = await markdown_coro
  # await markdown_proc.wait()

  print(f'Markdown output done.', file=sys.stderr)

  for output in pandoc_outputs:
    yield Task(
      func = pandoc_md_to_output,
      args = (uuid_ss_folder, timestamp, output)
    )