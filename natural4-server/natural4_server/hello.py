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
  Coroutine,
  Sequence
)
import datetime
import json
from multiprocessing import Process
import os
from pathlib import Path
import re
import subprocess
import sys
import typing

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

from aiostream import stream

import pyrsistent as pyrs
import pyrsistent.typing as pyrst

from flask import Flask, Response, request, send_file

from plugins.natural4_maude import get_maude_tasks
from plugins.docgen import get_pandoc_tasks
from plugins.flowchart import get_flowchart_tasks

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

try:
  v8k_workdir = Path(os.environ['V8K_WORKDIR'])
except KeyError:
  print(
    'V8K_WORKDIR not set in os.environ -- check your gunicorn config!!',
    file=sys.stderr
  )
  v8k_workdir = Path()

try:
  v8k_slots_arg: str = f'--poolsize {os.environ["V8K_SLOTS"]}'
except KeyError:
  v8k_slots_arg = ''

v8k_startport: str = os.environ.get('v8k_startport', '')

v8k_path: str = os.environ.get('v8k_path', '')

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

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

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

  response = empty_response
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

    mimetype: typing.Literal['text/plain'] | None = (
      'text/plain' if Path(filename).suffix in exts else None
    )
    mimetype_str: typing.Literal['text/plain', ''] = (
      mimetype if mimetype else ''
    )
    print(
      f'get_workdir_file: returning {mimetype_str} {workdir_folder_filename}',
      file=sys.stderr
    )
    response: Response = send_file(workdir_folder_filename, mimetype = mimetype)

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

  return pipe(
    temp_dir / 'workdir' / uuid / ssid / sid / 'aasvg' / 'LATEST' / image,
    do(lambda image_path:
        print(f'show_aasvg_image: sending path {image_path}', file=sys.stderr)),
    send_file
  )

@curry
async def run_tasks(
  tasks: AsyncGenerator[Coroutine, None]
) -> None:
  '''
  Runs tasks asynchronously in the background.
  '''

  try:
    async with (asyncio.timeout(20), asyncio.TaskGroup() as taskgroup):
      async for task in tasks:
        print(f'Running task: {task}', file=sys.stderr)
        taskgroup.create_task(task)
  except TimeoutError as exc:
    print(f'Timeout while generating outputs: {exc}', file=sys.stderr)

# ################################################
#                      main
#      HANDLE POSTED CSV, RUN NATURAL4 & ETC
# ################################################
# This is the function that does all the heavy lifting.

@app.route('/post', methods=['GET', 'POST'])
async def process_csv() -> str:
  start_time: datetime.datetime = datetime.datetime.now()
  print("\n--------------------------------------------------------------------------\n", file=sys.stderr)
  print("hello.py processCsv() starting at ", start_time, file=sys.stderr)

  data: pyrst.PMap[str, str] = pyrs.pmap(request.form)

  response: pyrst.PMap[str, str | None] = pyrs.m()

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

  with open(target_path, 'w') as fout:
    fout.write(data['csvString'])

  # Generate markdown files asynchronously in the background.
  uuiddir: Path = Path(uuid) / spreadsheet_id / sheet_id

  markdown_cmd: Sequence[str] = pyrs.v(
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
  create_files: Sequence[str] = pyrs.v(
    natural4_exe,
    '--tomd', '--toasp', '--toepilog',
    f'--workdir={natural4_dir}',
    f'--uuiddir={Path(uuid) / spreadsheet_id/ sheet_id}',
    f'{target_path}'
  )

  print(f'hello.py main: calling natural4-exe {natural4_exe}', file=sys.stderr)
  print(f'hello.py main: {" ".join(create_files)}', file=sys.stderr)

  nl4exe: subprocess.CompletedProcess[bytes] = subprocess.run(
    create_files,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
  )

  print(
    f'hello.py main: back from natural4-exe (took {datetime.datetime.now() - start_time})',
    file=sys.stderr
  )

  nl4_out, nl4_err = nl4exe.stdout.decode('utf-8'), nl4exe.stderr.decode('utf-8')

  print(f'hello.py main: natural4-exe stdout length = {len(nl4_out)}', file=sys.stderr)
  print(f'hello.py main: natural4-exe stderr length = {len(nl4_err)}', file=sys.stderr)

  short_err_maxlen, long_err_maxlen = 2_000, 20_000

  if len(nl4_err) < short_err_maxlen:
    print(nl4_err)

  with open(target_folder / f'{time_now}.err', 'w') as fout:
    fout.write(nl4_err)
  with open(target_folder / f'{time_now}.out', 'w') as fout:
    fout.write(nl4_out)

  response = response.set('nl4_stderr', nl4_err[:long_err_maxlen])
  response = response.set('nl4_stdout', nl4_out[:long_err_maxlen])

  # ---------------------------------------------
  # postprocessing: for petri nets: turn the DOT files into PNGs
  # we run this asynchronously and block at the end before returning.
  # ---------------------------------------------
  uuid_ss_folder: Path = temp_dir / "workdir" / uuid / spreadsheet_id / sheet_id
  petri_folder: Path = uuid_ss_folder / "petri"
  dot_path: Path = petri_folder / "LATEST.dot"
  timestamp = Path(dot_path.readlink().stem)

  flowchart_coro: Awaitable[None] = pipe(
    (uuid_ss_folder, timestamp),
    lambda x: get_flowchart_tasks(*x),
    run_tasks
  )

  # Slow tasks below.
  # Thes are forked into a separate process, in which they are run
  # asynchronously via the run_tasks coroutine.

  # ---------------------------------------------
  # postprocessing:
  # Use pandoc to generate word and pdf docs from markdown.
  # ---------------------------------------------

  pandoc_tasks: AsyncGenerator[Awaitable[None], None] = (
    get_pandoc_tasks(markdown_coro, uuid_ss_folder, timestamp)
  )

  # ---------------------------------------------
  # postprocessing:
  # Use Maude to generate the state space and find race conditions
  # ---------------------------------------------
  maude_output_path: Path = uuid_ss_folder / 'maude'
  natural4_file: Path = maude_output_path / 'LATEST.natural4'

  maude_tasks: AsyncGenerator[Awaitable[None], None] = (
    get_maude_tasks(natural4_file, maude_output_path)
  )

  slow_tasks = stream.chain(maude_tasks, pandoc_tasks)
  Process(
    target = compose_left(run_tasks, asyncio.run),
    args = (slow_tasks,)
  ).start()

  # ---------------------------------------------
  # postprocessing: (re-)launch the vue web server
  # - call v8k up
  # ---------------------------------------------
  v8kargs: Sequence[str] = pyrs.v(
    'python', v8k_path,
    f'--workdir={v8k_workdir}',
    'up',
    v8k_slots_arg,
    f'--uuid={uuid}',
    f'--ssid={spreadsheet_id}',
    f'--sheetid={sheet_id}',
    f'--startport={v8k_startport}',
    f'{uuid_ss_folder / "purs" / "LATEST.purs"}'
  )

  print(f'hello.py main: calling {" ".join(v8kargs)}', file=sys.stderr)

  with open(uuid_ss_folder / 'v8k.out', 'w+') as outfile:
    subprocess.run(
      # Joe: For some reason, passing these in as separate args results in the
      # following error:
      # usage: v8k [-h] [--workdir WORKDIR] {list,find,up,down,downdir} ...
      # v8k: error: unrecognized arguments: temp/workdir/e62c137a-38f1-4acc-ad13-44c1005eb523/1leBCZhgDsn-Abg2H_OINGGv-8Gpf9mzuX1RR56v0Sss/1779650637/purs/LATEST.purs
      [' '.join(v8kargs)], shell=True,
      stdout=outfile # stderr=outfile
    )

  print('hello.py main: v8k up returned', file=sys.stderr)
  with open(uuid_ss_folder / 'v8k.out', 'r') as read_file:
    v8k_out: str = read_file.readline()
  print(f'v8k.out: {v8k_out}', file=sys.stderr)

  print(
    f'to see v8k bring up vue using npm run serve, run\n  tail -f {(uuid_ss_folder / "v8k.out").resolve()}',
    file=sys.stderr
  )

  if re.match(r':\d+', v8k_out):  # we got back the expected :8001/uuid/ssid/sid whatever from the v8k call
    v8k_url: str = v8k_out.strip()
    print(f'v8k up succeeded with: {v8k_url}', file=sys.stderr)
    response = response.set('v8k_url', v8k_url)
  else:
    response = response.set('v8k_url', None)

  # ---------------------------------------------
  # load in the aasvg index HTML to pass back to sidebar
  # ---------------------------------------------

  with open(uuid_ss_folder / 'aasvg' / 'LATEST' / 'index.html', 'r') as read_file:
    response = response.set('aasvg_index', read_file.read())

  # ---------------------------------------------
  # construct other response elements and log run-timings.
  # ---------------------------------------------

  response = response.set('timestamp', f'{timestamp}')

  end_time: datetime.datetime = datetime.datetime.now()
  elapsed_time: datetime.timedelta = end_time - start_time

  print(
    f'hello.py process_csv ready to return at {end_time} (total {elapsed_time})',
    file=sys.stderr
  )

  # print(
  #   "hello.py processCsv parent returning at ", datetime.datetime.now(), "(total",
  #   datetime.datetime.now() - start_time, ")",
  #   file=sys.stderr
  # )

  # if this leads to trouble we may need to double-fork with grandparent-wait
  # if childpid > 0:  # in the parent
    # print("hello.py processCsv parent returning at", datetime.datetime.now(),
    #                   "(total", datetime.datetime.now() - start_time, ")", file=sys.stderr)
  # print("hello.py processCsv parent returning at ", datetime.datetime.now(), "(total",
  #       datetime.datetime.now() - start_time, ")", file=sys.stderr)
  # print(json.dumps(response), file=sys.stderr)

  # else:  # in the child
  # print('hello.py processCsv: fork(child): continuing to run', file=sys.stderr)

  # print("hello.py child: returning at", datetime.datetime.now(), "(total", datetime.datetime.now() - start_time,
  #       ")", file=sys.stderr)

  # Block and wait for the flowcharts to be generated before returning.
  await flowchart_coro

  return json.dumps(pyrs.thaw(response))

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
