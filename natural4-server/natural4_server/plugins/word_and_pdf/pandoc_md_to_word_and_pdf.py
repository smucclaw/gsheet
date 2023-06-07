import os
import sys
from pathlib import Path
import _typeshed

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

import pyrsistent as pyrs

import pypandoc

class PandocOutput(pyrs.PRecord):
  file_extension = pyrs.field(mandatory = True, type = str)
  extra_args = pyrs.pvector_field(
    str, optional = True, initial = pyrs.pvector()
  )

outputs: pyrs.PVector[PandocOutput] = pyrs.v(
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
def pandoc_md_to_word_and_pdf(
  uuid_ss_folder: _typeshed.StrOrBytesPath,
  timestamp: str
) -> None:
  uuid_ss_folder_path = Path(uuid_ss_folder)
  md_file = uuid_ss_folder_path / 'md' / 'LATEST.md' # f'{timestamp}.md'
  # pipe(
  #   uuid_ss_folder_path / 'md',
  #   do(lambda x: x.mkdir(parents=True, exist_ok=True)),
  #   lambda x: x / f'{timestamp}.md'

  for output in outputs:
    match output:
      case {'file_extension': file_extension, 'extra_args': extra_args}:
        outputpath:Path = uuid_ss_folder_path / file_extension
        outputpath.mkdir(parents=True, exist_ok=True)

        timestamp_file = Path(f'{timestamp}.{file_extension}')
        outputfile = str(outputpath / timestamp_file)

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