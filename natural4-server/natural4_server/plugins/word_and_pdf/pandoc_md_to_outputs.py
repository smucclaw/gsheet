import asyncio
import os
import sys
from pathlib import Path

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

import pyrsistent as pyrs
import pyrsistent.typing as pyrst

import pypandoc

class PandocOutput(pyrs.PRecord):
  file_extension = pyrs.field(mandatory = True, type = str)
  extra_args = pyrs.pvector_field(
    str, optional = True, initial = pyrs.pvector()
  )

pandoc_outputs:pyrst.PSet[PandocOutput] = pyrs.s(
  PandocOutput(
    file_extension = 'docx',
    extra_args = pyrs.v(
      '-f', 'markdown+hard_line_breaks',
      '-s'
    )
  ),
  PandocOutput(
    file_extension = 'pdf',
    extra_args = pyrs.v(
      '--pdf-engine=xelatex',
      '-V', 'CJKmainfont=Droid Sans Fallback',
      '-f', 'markdown+hard_line_breaks',
      '-s'
    )
  )
)

@curry
def pandoc_md_to_output(
  uuid_ss_folder: str | os.PathLike,
  timestamp: str,
  pandoc_output: PandocOutput
) -> None:
  uuid_ss_folder_path = Path(uuid_ss_folder)
  md_file = uuid_ss_folder_path / 'md' / 'LATEST.md' # f'{timestamp}.md'
  # pipe(
  #   uuid_ss_folder_path / 'md',
  #   do(lambda x: x.mkdir(parents=True, exist_ok=True)),
  #   lambda x: x / f'{timestamp}.md'
  if md_file.exists():
    match pandoc_output:
      case {'file_extension': file_extension, 'extra_args': extra_args}:
        outputpath:Path = uuid_ss_folder_path / file_extension
        outputpath.mkdir(parents=True, exist_ok=True)

        timestamp_file = f'{timestamp}.{file_extension}'
        outputfile = f'{outputpath / timestamp_file}'

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

        latest_file = outputpath / f'LATEST.{file_extension}'
        if latest_file.exists():
          os.unlink(latest_file)
        os.symlink(timestamp_file, latest_file)

@curry
async def pandoc_md_to_outputs(
  uuid_ss_folder: str | os.PathLike,
  timestamp: str
) -> None:
  try:
    async with (asyncio.timeout(15), asyncio.TaskGroup() as tasks):
      for pandoc_output in pandoc_outputs:
        pipe(
          (pandoc_md_to_output, uuid_ss_folder, timestamp, pandoc_output),
          lambda x: asyncio.to_thread(*x),
          tasks.create_task
        )
  except TimeoutError:
    print("Pandoc timeout", file=sys.stderr)

@curry
def run_pandoc_md_to_outputs(
  uuid_ss_folder: str | os.PathLike,
  timestamp: str
) -> None:
  asyncio.run(pandoc_md_to_outputs(uuid_ss_folder, timestamp))