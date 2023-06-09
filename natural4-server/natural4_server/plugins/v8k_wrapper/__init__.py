# https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path

from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from importlib.machinery import ModuleSpec
from pathlib import Path
import importlib.util
import os
import sys
from types import ModuleType

from cytoolz.functoolz import curry

import pyrsistent

v8k_path: str = os.environ.get('v8k_path', '')

spec: ModuleSpec | None = importlib.util.spec_from_file_location(
  name='v8k', location=v8k_path
)

print(f'v8k spec: {spec}', file=sys.stderr)

if not spec or not spec.loader:
  @curry
  def v8k_main(
    uuid: str,
    spreadsheet_id: str,
    sheet_id: str,
    uuid_ss_folder: str | os.PathLike
  ) -> None:
    return
else:
  # Dynamically load and import v8k from its path.
  print(f'Loading v8k from {v8k_path}', file=sys.stderr)
  v8k: ModuleType = importlib.util.module_from_spec(spec)
  sys.modules['v8k'] = v8k
  spec.loader.exec_module(v8k)

  try:
    v8k_workdir: Path = Path(os.environ['V8K_WORKDIR'])
  except KeyError:
    print(
      'V8K_WORKDIR not set in os.environ -- check your gunicorn config!!',
      file=sys.stderr
    )
    v8k_workdir: Path = Path()

  try:
    v8k_slots_arg: str = f'--poolsize {os.environ["V8K_SLOTS"]}'
  except KeyError:
    v8k_slots_arg = ''

  v8k_startport: str = os.environ.get('v8k_startport', '')

  @curry
  def v8k_main(
    uuid: str,
    spreadsheet_id: str,
    sheet_id: str,
    uuid_ss_folder: str | os.PathLike
  ) -> None:
    v8k_args: Sequence[str] = pyrsistent.v(
      # 'python', v8k_path,
      f'--workdir={v8k_workdir}',
      'up',
      v8k_slots_arg,
      f'--uuid={uuid}',
      f'--ssid={spreadsheet_id}',
      f'--sheetid={sheet_id}',
      f'--startport={v8k_startport}',
      f'{Path(uuid_ss_folder) / "purs" / "LATEST.purs"}'
    )
    
    print(f'hello.py main: calling v8k with {" ".join(v8k_args)}', file=sys.stderr)

    parser: ArgumentParser = v8k.setup_argparser()
    args: Namespace = parser.parse_args(args = v8k_args)

    if not hasattr(args, 'func'):
      print("v8k: list / find / up / down / downdir")
      if "V8K_WORKDIR" in os.environ:
        print(f"V8K_WORKDIR = {os.environ['V8K_WORKDIR']}")
    else:
      if args.workdir is not None:
        workdir = args.workdir
      elif "V8K_WORKDIR" in os.environ:
        workdir = os.environ["V8K_WORKDIR"]
      else:
        print("v8k: you need to export V8K_WORKDIR=\"/home/something/multivue\"", file=sys.stderr)
        return
      args.func(args, workdir)