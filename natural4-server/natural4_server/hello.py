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
from collections.abc import Sequence, Mapping
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

import pyrsistent as pyrs
import pyrsistent.typing as pyrst

from flask import Flask, Response, request, send_file

from plugins.natural4_maude import run_analyse_state_space
from plugins.word_and_pdf import run_pandoc_md_to_outputs
from plugins.flowchart import run_flowchart_dot_to_outputs

##########################################################
# SETRLIMIT to kill gunicorn runaway workers after a certain number of cpu seconds
# cargo-culted from https://www.geeksforgeeks.org/python-how-to-put-limits-on-memory-and-cpu-usage/
##########################################################

import signal
import resource
  
# checking time limit exceed
def time_exceeded(signo, frame):
  print("hello.py: setrlimit time exceeded, exiting")
  raise SystemExit(1)
  
def set_max_runtime(seconds):
  # setting up the resource limit
  soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
  resource.setrlimit(resource.RLIMIT_CPU, (seconds, hard))
  signal.signal(signal.SIGXCPU, time_exceeded)
  
# max run time
set_max_runtime(10000)

########################################################## end of setrlimit

from plugins.natural4_maude import run_analyse_state_space

basedir = Path(os.environ.get("basedir", "."))

if "V8K_WORKDIR" in os.environ:
  v8k_workdir = os.environ["V8K_WORKDIR"]
else:
  print("V8K_WORKDIR not set in os.environ -- check your gunicorn config!!", file=sys.stderr)

if "V8K_SLOTS" in os.environ:
  v8k_slots_arg = "--poolsize " + os.environ["V8K_SLOTS"]
else:
  v8k_slots_arg = ""

if "v8k_startport" in os.environ:
  v8k_startport = os.environ["v8k_startport"]

if "v8k_path" in os.environ:
  v8k_path = os.environ["v8k_path"]


default_filenm_natL4exe_from_stack_install = "natural4-exe"
natural4_exe = os.environ.get("natural4_exe", default_filenm_natL4exe_from_stack_install)
# sometimes it is desirable to override the default name
# that `stack install` uses with a particular binary from a particular commit
# in which case you would set up gunicorn.conf.py with a natural4_exe = natural4-noqns or something like that


# see gunicorn.conf.py for basedir, workdir, startport
template_dir:Path = basedir / "template"
temp_dir:Path = basedir / "temp"
static_dir:Path = basedir / "static"
natural4_dir:Path = temp_dir / "workdir"

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
  print("get_workdir_file: handling request for %s/%s/%s/%s/%s" % (uuid, ssid, sid, channel, filename), file=sys.stderr)
  workdir_folder:Path = temp_dir / "workdir" / uuid / ssid / sid / channel
  match (workdir_folder.exists(), (workdir_folder / filename).is_file()):
    case (False, _):
      print("get_workdir_file: unable to find workdir_folder " + workdir_folder, file=sys.stderr)
    case (__, False):
      print("get_workdir_file: unable to find file %s/%s" % (workdir_folder, filename), file=sys.stderr)
    case _:
      exts:pyrst.PSet[str] = pyrs.s(
        '.l4', '.epilog', '.purs', '.org', '.hs', '.ts', '.natural4'
      )
      if Path(filename).suffix in exts:
        print("get_workdir_file: returning text/plain %s/%s" % (workdir_folder, filename), file=sys.stderr)
        mimetype = 'text/plain'
      else:
        print("get_workdir_file: returning %s/%s" % (workdir_folder, filename), file=sys.stderr)
        mimetype = None
      return send_file(workdir_folder / filename, mimetype=mimetype)

  # if not os.path.exists(workdir_folder):
  #   print("get_workdir_file: unable to find workdir_folder " + workdir_folder, file=sys.stderr)
  # elif not os.path.isfile(workdir_folder + "/" + filename):
  #   print("get_workdir_file: unable to find file %s/%s" % (workdir_folder, filename), file=sys.stderr)
  # else:
  #   (_, ext) = os.path.splitext(filename)
  #   if ext in {".l4", ".epilog", ".purs", ".org", ".hs", ".ts", ".natural4"}:
  #     print("get_workdir_file: returning text/plain %s/%s" % (workdir_folder, filename), file=sys.stderr)
  #     mimetype = 'text/plain'
  #   else:
  #     print("get_workdir_file: returning %s/%s" % (workdir_folder, filename), file=sys.stderr)
  #     mimetype = None
  #   return send_file(workdir_folder + "/" + filename, mimetype=mimetype)

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
  print("show_aasvg_image: handling request for /aasvg/ url", file=sys.stderr)
  return pipe(
    temp_dir / 'workdir' / uuid / ssid / sid / 'aasvg' / 'LATEST' / image,
    do(lambda image_path:
        print(f'show_aasvg_image: sending path {image_path}', file=sys.stderr)),
    send_file
  )

# ################################################
#                      main
#      HANDLE POSTED CSV, RUN NATURAL4 & ETC
# ################################################
# This is the function that does all the heavy lifting.

@app.route('/post', methods=['GET', 'POST'])
async def process_csv() -> str:
  start_time = datetime.datetime.now()
  print("\n--------------------------------------------------------------------------\n", file=sys.stderr)
  print("hello.py processCsv() starting at ", start_time, file=sys.stderr)

  data: Mapping[str, str] = request.form.to_dict()

  response: Mapping[str, str] = {}

  uuid = data['uuid']
  spreadsheet_id = data['spreadsheetId']
  sheet_id = data['sheetId']
  target_folder = Path(natural4_dir) / uuid / spreadsheet_id / sheet_id
  print(target_folder)
  time_now = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S.%fZ")
  target_file = Path(f'{time_now}.csv')
  target_path = target_folder / target_file

  target_folder.mkdir(parents=True, exist_ok=True)

  with open(target_path, 'w') as fout:
    fout.write(data['csvString'])

  # target_path is for CSV data

  # ---------------------------------------------
  # call natural4-exe, wait for it to complete. see SECOND RUN below.
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
  nl4exe = subprocess.run(
    create_files,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
  )
  print("hello.py main: back from natural4-exe (took", datetime.datetime.now() - start_time, ")", file=sys.stderr)

  nl4_out, nl4_err = nl4exe.stdout.decode('utf-8'), nl4exe.stderr.decode('utf-8')

  print(f"hello.py main: natural4-exe stdout length = {len(nl4_out)}", file=sys.stderr)
  print(f"hello.py main: natural4-exe stderr length = {len(nl4_err)}", file=sys.stderr)

  short_err_maxlen, long_err_maxlen = 2_000, 20_000

  if len(nl4_err) < short_err_maxlen:
    print(nl4_err)

  with open(target_folder / f'{time_now}.err', "w") as fout:
    fout.write(nl4_err)
  with open(target_folder / f'{time_now}.out', "w") as fout:
    fout.write(nl4_out)

  response['nl4_stderr'] = nl4_err[:long_err_maxlen]
  response['nl4_stdout'] = nl4_out[:long_err_maxlen]

  # ---------------------------------------------
  # postprocessing: for petri nets: turn the DOT files into PNGs
  # ---------------------------------------------

  uuid_ss_folder = temp_dir / "workdir" / uuid / spreadsheet_id / sheet_id
  petri_folder = uuid_ss_folder / "petri"
  dot_path = petri_folder / "LATEST.dot"
  # (timestamp, ext) = os.path.splitext(os.readlink(dot_path))
  timestamp = dot_path.resolve()

  flowchart_outputs = run_flowchart_dot_to_outputs(uuid_ss_folder, timestamp)

  # if not os.path.exists(petri_folder):
  #   print("expected to find petri_folder %s but it's not there!" % (petri_folder), file=sys.stderr)
  # else:
  #   petri_path_svg = petri_folder + timestamp + ".svg"
  #   petri_path_png = petri_folder + timestamp + ".png"
  #   small_petri_path = petri_folder + timestamp + "-small.png"
  #   print("hello.py main: running: dot -Tpng -Gdpi=150 " + dot_path + " -o " + petri_path_png + " &", file=sys.stderr)
  #   os.system("dot -Tpng -Gdpi=72  " + dot_path + " -o " + small_petri_path + " &")
  #   os.system("dot -Tpng -Gdpi=150 " + dot_path + " -o " + petri_path_png + " &")
  #   os.system("dot -Tsvg           " + dot_path + " -o " + petri_path_svg + " &")
  #   try:
  #     if os.path.isfile(petri_folder + "LATEST.svg"):       os.unlink(petri_folder + "LATEST.svg")
  #     if os.path.isfile(petri_folder + "LATEST.png"):       os.unlink(petri_folder + "LATEST.png")
  #     if os.path.isfile(petri_folder + "LATEST-small.png"): os.unlink(petri_folder + "LATEST-small.png")
  #     os.symlink(os.path.basename(petri_path_svg), petri_folder + "LATEST.svg")
  #     os.symlink(os.path.basename(petri_path_png), petri_folder + "LATEST.png")
  #     os.symlink(os.path.basename(small_petri_path), petri_folder + "LATEST-small.png")
  #   except Exception as e:
  #     print("hello.py main: got some kind of OS error to do with the unlinking and the symlinking",
  #           file=sys.stderr)
  #     print("hello.py main: %s" % (e), file=sys.stderr)

  # ---------------------------------------------
  # postprocessing: call pandoc to convert markdown to pdf and word docs
  # ---------------------------------------------
  pandoc_outputs = run_pandoc_md_to_outputs(uuid_ss_folder, timestamp)

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

  print("hello.py main: calling %s" % (" ".join(v8kargs)), file=sys.stderr)

  with open(uuid_ss_folder / 'v8k.out', 'w+') as outfile:
    subprocess.run(
      # Joe: For some reason, passing these in as separate args results in the
      # following error:
      # usage: v8k [-h] [--workdir WORKDIR] {list,find,up,down,downdir} ...
      # v8k: error: unrecognized arguments: temp/workdir/e62c137a-38f1-4acc-ad13-44c1005eb523/1leBCZhgDsn-Abg2H_OINGGv-8Gpf9mzuX1RR56v0Sss/1779650637/purs/LATEST.purs
      [' '.join(v8kargs)], shell=True,
      stdout=outfile # stderr=outfile
    )

  # os.system(' '.join(v8kargs))
  # os.system(" ".join(v8kargs) + "> " + uuid_ss_folder + "/v8k.out")
  print('hello.py main: v8k up returned', file=sys.stderr)
  with open(uuid_ss_folder / 'v8k.out', "r") as read_file:
    v8k_out = read_file.readline()
  print(f"v8k.out: {v8k_out}", file=sys.stderr)

  print(
    f'to see v8k bring up vue using npm run serve, run\n  tail -f {(uuid_ss_folder / "v8k.out").resolve()}',
    file=sys.stderr
  )

  if re.match(r':\d+', v8k_out):  # we got back the expected :8001/uuid/ssid/sid whatever from the v8k call
    v8k_url = v8k_out.strip()
    print(f"v8k up succeeded with: {v8k_url}", file=sys.stderr)
    response['v8k_url'] = v8k_url
  else:
    response['v8k_url'] = None

# ---------------------------------------------
# load in the aasvg index HTML to pass back to sidebar
# ---------------------------------------------

  with open(uuid_ss_folder / "aasvg" / "LATEST" / "index.html", "r") as read_file:
    response['aasvg_index'] = read_file.read()

# ---------------------------------------------
# construct other response elements and log run-timings.
# ---------------------------------------------

  response['timestamp'] = f'{timestamp}'

  end_time = datetime.datetime.now()
  elapsed_time = end_time - start_time

  print("hello.py processCsv ready to return at", end_time, "(total", elapsed_time, ")", file=sys.stderr)

# ---------------------------------------------
# call natural4-exe; this is the SECOND RUN for any slow transpilers
# ---------------------------------------------

  print("hello.py processCsv parent returning at ", datetime.datetime.now(), "(total",
        datetime.datetime.now() - start_time, ")", file=sys.stderr)

  childpid = os.fork()

  # if this leads to trouble we may need to double-fork with grandparent-wait
  if childpid > 0:  # in the parent
    # print("hello.py processCsv parent returning at", datetime.datetime.now(),
    #                   "(total", datetime.datetime.now() - start_time, ")", file=sys.stderr)
    print("hello.py processCsv parent returning at ", datetime.datetime.now(), "(total",
          datetime.datetime.now() - start_time, ")", file=sys.stderr)
    # print(json.dumps(response), file=sys.stderr)

    async with asyncio.TaskGroup() as tasks:
      tasks.create_task(flowchart_outputs)
      tasks.create_task(pandoc_outputs)

    return json.dumps(response)
  else:  # in the child
    print("hello.py processCsv: fork(child): continuing to run", file=sys.stderr)

    create_files: Sequence[str] = pyrs.v(
      natural4_exe,
      '--only', 'tomd', f'--workdir={natural4_dir}',
      f'--uuiddir={Path(uuid) / spreadsheet_id / sheet_id}',
      f'{target_path}'
    )
    print(f"hello.py child: calling natural4-exe {natural4_exe} (slowly) for tomd", file=sys.stderr)
    print(f"hello.py child: {create_files}", file=sys.stderr)
    nl4exe = subprocess.run(
      create_files,
      stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    print("hello.py child: back from slow natural4-exe 1 (took", datetime.datetime.now() - start_time, ")",
          file=sys.stderr)
    print(f'hello.py child: natural4-exe stdout length = {len(nl4exe.stdout.decode("utf-8"))}', file=sys.stderr)
    print(f'hello.py child: natural4-exe stderr length = {len(nl4exe.stderr.decode("utf-8"))}', file=sys.stderr)

    print("hello.py child: returning at", datetime.datetime.now(), "(total", datetime.datetime.now() - start_time,
          ")", file=sys.stderr)

    maude_output_path = uuid_ss_folder / 'maude'
    natural4_file = maude_output_path / 'LATEST.natural4'

    maude_outputs = run_analyse_state_space(natural4_file, maude_output_path)

    await maude_outputs

    # async with asyncio.TaskGroup() as tasks:
    #   tasks.create_task(flowchart_outputs)
    #   tasks.create_task(pandoc_outputs)
    #   tasks.create_task(maude_outputs)

    # this return shouldn't mean anything because we're in the child, but gunicorn may somehow pick it up?
    return json.dumps(response)

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
