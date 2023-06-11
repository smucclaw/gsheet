# ################################################
#               ONLINE DOCUMENTATION
# ################################################
# please see https://docs.google.com/document/d/1EvyiQhSgapumBRt9UloRpwiRcgVhF-m65FVdAz3chfs/edit#
# software version: 1.1.3

# ################################################
#          INVOCATION AND CONFIGURATION
# ################################################
# There is no #! line because we are run out of gunicorn.

import asyncio
from collections.abc import (
  AsyncGenerator,
  Awaitable,
  Collection,
  Sequence
)
import datetime
import os
from pathlib import Path
import sys
import typing

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

import aiofiles
import aiostream

import pyrsistent as pyrs
import pyrsistent.typing as pyrst

# from flask import Flask, Response, request, send_file
from quart import Quart, Response, request, send_file

from natural4_server.task import Task, add_tasks_to_background, run_tasks
from plugins.docgen import get_pandoc_tasks
from plugins.flowchart import get_flowchart_tasks
from plugins.natural4_maude import get_maude_tasks
import plugins.v8k as v8k

##########################################################
# SETRLIMIT to kill gunicorn runaway workers after a certain number of cpu seconds
# cargo-culted from https://www.geeksforgeeks.org/python-how-to-put-limits-on-memory-and-cpu-usage/
##########################################################

import signal
import resource

# checking time limit exceed
def time_exceeded(signo, frame) -> typing.NoReturn:
  print("hello.py: setrlimit time exceeded, exiting")
  raise SystemExit(1)

def set_max_runtime(seconds) -> None:
  # setting up the resource limit
  soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
  resource.setrlimit(resource.RLIMIT_CPU, (seconds, hard))
  signal.signal(signal.SIGXCPU, time_exceeded)

# max run time
set_max_runtime(10000)

########################################################## end of setrlimit

basedir = Path(os.environ.get("basedir", "."))

default_filenm_natL4exe_from_stack_install = "natural4-exe"
natural4_exe: str = os.environ.get('natural4_exe', default_filenm_natL4exe_from_stack_install)

# sometimes it is desirable to override the default name
# that `stack install` uses with a particular binary from a particular commit
# in which case you would set up gunicorn.conf.py with a natural4_exe = natural4-noqns or something like that

# see gunicorn.conf.py for basedir, workdir, startport
template_dir: Path = basedir / "template"
temp_dir: Path = basedir / "temp"
static_dir: Path = basedir / "static"
natural4_dir: Path = temp_dir / "workdir"

app = Quart(__name__, template_folder=template_dir, static_folder=static_dir)

# ################################################
#            SERVE (MOST) STATIC FILES
# ################################################
#  secondary handler serves .l4, .md, .hs, etc static files

@app.route("/workdir/<uuid>/<ssid>/<sid>/<channel>/<filename>")
async def get_workdir_file(
  uuid: str | os.PathLike,
  ssid: str | os.PathLike,
  sid: str | os.PathLike,
  channel: str | os.PathLike,
  filename: str | os.PathLike
) -> Response:
  print(
    f'get_workdir_file: handling request for {uuid}/{ssid}/{sid}/{channel}/{filename}',
    file=sys.stderr
  )

  workdir_folder: Path = temp_dir / 'workdir' / uuid / ssid / sid / channel
  workdir_folder_filename: Path = workdir_folder / filename
  empty_response: Response = Response(status = 204)

  response: Response = empty_response
  if not workdir_folder.exists():
    print(
      f'get_workdir_file: unable to find workdir_folder {workdir_folder}',
      file=sys.stderr
    )
  elif not workdir_folder_filename.is_file():
    print(
      f'get_workdir_file: unable to find file {workdir_folder_filename}',
      file=sys.stderr
    )
  else:
    exts: Collection[str] = pyrs.s(
      '.l4', '.epilog', '.purs', '.org', '.hs', '.ts', '.natural4'
    )

    mimetype = 'text/plain' if Path(filename).suffix in exts else None
    mimetype_str = mimetype if mimetype else ''
    print(
      f'get_workdir_file: returning {mimetype_str} {workdir_folder_filename}',
      file=sys.stderr
    )
    response: Response = await send_file(
      workdir_folder_filename,
      mimetype = mimetype
    )

  return response

# ################################################
#            SERVE SVG STATIC FILES
# ################################################
# this is handled a little differently because
# the directory structure for SVG output is a bit
# more complicated than for the other outputs.
# There is a LATEST directory instead of a LATEST file
# so the directory path is a little bit different.

@app.route('/aasvg/<uuid>/<ssid>/<sid>/<image>')
async def show_aasvg_image(
  uuid: str | os.PathLike,
  ssid: str | os.PathLike,
  sid: str | os.PathLike,
  image: str | os.PathLike
) -> Response:
  print('show_aasvg_image: handling request for /aasvg/ url', file=sys.stderr)

  image_path = temp_dir / 'workdir' / uuid / ssid / sid / 'aasvg' / 'LATEST' / image
  print(f'show_aasvg_image: sending path {image_path}', file=sys.stderr)

  return await send_file(image_path)

# ################################################
#                      main
#      HANDLE POSTED CSV, RUN NATURAL4 & ETC
# This is the function that does all the heavy lifting.
@app.route('/post', methods=['GET', 'POST'])
async def process_csv() -> str:
  start_time: datetime.datetime = datetime.datetime.now()
  print("\n--------------------------------------------------------------------------\n", file=sys.stderr)
  print("hello.py processCsv() starting at ", start_time, file=sys.stderr)

  data: pyrst.PMap[str, str] = pyrs.pmap(await request.form)

  uuid: str = data['uuid']
  spreadsheet_id: str = data['spreadsheetId']
  sheet_id: str = data['sheetId']
  target_folder: Path = Path(natural4_dir) / uuid / spreadsheet_id / sheet_id
  print(target_folder)
  time_now: str = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S.%fZ")
  target_file = Path(f'{time_now}.csv')
  # target_path is for CSV data
  target_path: Path = target_folder / target_file

  target_folder.mkdir(parents=True, exist_ok=True)

  async with aiofiles.open(target_path, 'w') as fout:
    await fout.write(data['csvString'])

  # Generate markdown files asynchronously in the background.
  uuiddir: Path = Path(uuid) / spreadsheet_id / sheet_id

  markdown_cmd: Sequence[str] = (
    natural4_exe,
    '--only', 'tomd', f'--workdir={natural4_dir}',
    f'--uuiddir={uuiddir}',
    f'{target_path}'
  )

  print(f'hello.py child: calling natural4-exe {natural4_exe} (slowly) for tomd', file=sys.stderr)
  print(f'hello.py child: {markdown_cmd}', file=sys.stderr)

  # Coroutine which is awaited before pandoc is called to generate documents
  # (ie word and pdf) from the markdown file.
  markdown_coro: Awaitable[asyncio.subprocess.Process] = (
    asyncio.subprocess.create_subprocess_exec(
      *markdown_cmd,
      stdout = asyncio.subprocess.PIPE,
      stderr = asyncio.subprocess.PIPE
    )
  )

  # ---------------------------------------------
  # call natural4-exe, wait for it to complete.
  # ---------------------------------------------

  # one can leave out the markdown by adding the --tomd option
  # one can leave out the ASP by adding the --toasp option
  create_files: Sequence[str] = (
    natural4_exe,
    '--tomd', '--toasp', '--toepilog',
    f'--workdir={natural4_dir}',
    f'--uuiddir={Path(uuid) / spreadsheet_id/ sheet_id}',
    f'{target_path}'
  )

  print(f'hello.py main: calling natural4-exe {natural4_exe}', file=sys.stderr)
  print(f'hello.py main: {" ".join(create_files)}', file=sys.stderr)

  nl4exe = (
    await asyncio.subprocess.create_subprocess_exec(
      *create_files,
      stdout = asyncio.subprocess.PIPE,
      stderr = asyncio.subprocess.PIPE
    )
  )

  print(
    f'hello.py main: back from natural4-exe (took {datetime.datetime.now() - start_time})',
    file=sys.stderr
  )

  nl4_out, nl4_err = await nl4exe.communicate()
  nl4_out, nl4_err = nl4_out.decode(), nl4_err.decode()
  nl4_stdout, nl4_stderr = nl4_out[:long_err_maxlen], nl4_err[:long_err_maxlen]

  print(f'hello.py main: natural4-exe stdout length = {len(nl4_out)}', file=sys.stderr)
  print(f'hello.py main: natural4-exe stderr length = {len(nl4_err)}', file=sys.stderr)

  short_err_maxlen, long_err_maxlen = 2_000, 20_000

  if len(nl4_err) < short_err_maxlen:
    print(nl4_err)

  # response = response.set('nl4_stderr', nl4_err[:long_err_maxlen])
  # response = response.set('nl4_stdout', nl4_out[:long_err_maxlen])

  # ---------------------------------------------
  # postprocessing: for petri nets: turn the DOT files into PNGs
  # we run this asynchronously and block at the end before returning.
  # ---------------------------------------------
  uuid_ss_folder: Path = temp_dir / 'workdir' / uuid / spreadsheet_id / sheet_id
  petri_folder: Path = uuid_ss_folder / 'petri'
  dot_path: Path = petri_folder / 'LATEST.dot'
  timestamp: Path = Path(dot_path.readlink().stem)

  flowchart_coro: Awaitable[None] = pipe(
    (uuid_ss_folder, timestamp),
    lambda x: get_flowchart_tasks(*x),
    run_tasks
  )

  # Slow tasks below.
  # These are run in the background using app.add_background_task, which
  # adds them to Quart's event loop.

  # ---------------------------------------------
  # postprocessing:
  # Use pandoc to generate word and pdf docs from markdown.
  # ---------------------------------------------
  pandoc_tasks: AsyncGenerator[Task, None] = (
    get_pandoc_tasks(markdown_coro, uuid_ss_folder, timestamp)
  )

  # ---------------------------------------------
  # postprocessing:
  # Use Maude to generate the state space and find race conditions
  # ---------------------------------------------
  maude_output_path: Path = uuid_ss_folder / 'maude'
  natural4_file: Path = maude_output_path / 'LATEST.natural4'

  maude_tasks: AsyncGenerator[Task, None] = (
    get_maude_tasks(natural4_file, maude_output_path)
  )

  print('Running v8k', file=sys.stderr)

  # Concurrently peform the following:
  # - Schedule the slow Maude and pandoc tasks.
  # - Write natural4-exe's stdout to a file.
  # - Write natural4-exe's stderr to a file.
  # - Load the aasvg HTML which will later be sent back to the sidebar. 
  # - Run v8k up.
  async with (
    aiofiles.open(uuid_ss_folder / 'aasvg' / 'LATEST' / 'index.html', 'r')
    as aasvg_file,
    aiofiles.open(target_folder / f'{time_now}.err', 'w') as err_file,
    aiofiles.open(target_folder / f'{time_now}.out', 'w') as out_file,
    asyncio.TaskGroup() as taskgroup
  ):
    taskgroup.create_task(add_tasks_to_background(maude_tasks))
    taskgroup.create_task(add_tasks_to_background(pandoc_tasks))
    taskgroup.create_task(err_file.write(nl4_err))
    taskgroup.create_task(out_file.write(nl4_out))

    aasvg_index_task = taskgroup.create_task(aasvg_file.read())

    v8k_task = taskgroup.create_task(
      v8k.main(
        'up', uuid, spreadsheet_id, sheet_id, uuid_ss_folder
      )
    )

  match v8k_task.result():
    case {
      'port': v8k_port,
      'base_url': v8k_base_url,
      'vue_purs_tasks': vue_purs_tasks
    }:
      v8k_url = f':{v8k_port}{v8k_base_url}'
      vue_purs_tasks = vue_purs_tasks
    # Fall-through case in case v8k up didn't return a result or returned an
    # empty result.
    case _:
      v8k_url = None
      vue_purs_tasks = aiostream.stream.empty()

  # response = response.set('v8k_url', v8k_url)

  print('hello.py main: v8k up returned', file=sys.stderr)
  if v8k_url:
    print(f'v8k up succeeded with: {v8k_url}', file=sys.stderr)

  print(f'to see v8k bring up vue using npm run serve, run\n  tail -f {(uuid_ss_folder / "v8k.out").resolve()}',file=sys.stderr)

  add_tasks_to_background(vue_purs_tasks)

  # app.add_background_task(compose_left(run_tasks, asyncio.run), slow_tasks)

  # ---------------------------------------------
  # construct other response elements and log run-timings.
  # ---------------------------------------------

  end_time: datetime.datetime = datetime.datetime.now()
  elapsed_time: datetime.timedelta = end_time - start_time

  print(
    f'hello.py process_csv ready to return at {end_time} (total {elapsed_time})',
    file=sys.stderr
  )

  # Wait for the flowcharts to be generated before returning to the sidebar.
  await flowchart_coro

  return {
    'nl4_stdout': nl4_stdout,
    'nl4_err': nl4_stderr,
    'v8k_url': v8k_url,
    'aasvg_index': aasvg_index_task.result(),
    'timestamp': f'{timestamp}'
  }

  # ---------------------------------------------
  # return to sidebar caller
  # ---------------------------------------------

# ################################################
# run when not launched via gunicorn
# ################################################

# This should only be ran while in debugging, and not in production
# The debugging werkzeug server cannot have be both a multi-threaded
# and multi-process at the same time.
# For local development purposes this running it as a
# multi-process server is fine, change if needed
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=False, threaded=False, processes=6)
