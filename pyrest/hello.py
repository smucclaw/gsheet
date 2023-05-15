# ################################################
#               ONLINE DOCUMENTATION
# ################################################
# please see https://docs.google.com/document/d/1EvyiQhSgapumBRt9UloRpwiRcgVhF-m65FVdAz3chfs/edit#
# software version: 1.1.3

# ################################################
#          INVOCATION AND CONFIGURATION
# ################################################
# There is no #! line because we are run out of gunicorn.

import datetime
import json
import os
import re
import subprocess
import sys
# import threading
import asyncio
from pathlib import Path

from flask import Flask, request, send_file

import natural4_maude.visualise as maude_vis

if "basedir" in os.environ:
    basedir = os.environ["basedir"]
if "V8K_WORKDIR" in os.environ:
    v8k_workdir = os.environ["V8K_WORKDIR"]
if "v8k_startport" in os.environ:
    v8k_startport = os.environ["v8k_startport"]
if "v8k_path" in os.environ:
    v8k_path = os.environ["v8k_path"]
if "natural4_ver" in os.environ:
    natural4_ver = os.environ["v8k_path"]
else:
    natural4_ver = "natural4-exe"

natural4_exe = "natural4-exe"  # the default filename when you call `stack install`
# but sometimes it is desirable to override it with a particular binary from a particular commit
# in which case you would set up gunicorn.conf.py with a natural4_exe = natural4-noqns or something like that
if "natural4_exe" in os.environ: natural4_exe = os.environ["natural4_exe"]

# if "maudedir" in os.environ: maudedir = os.environ["maudedir"]

# see gunicorn.conf.py for basedir, workdir, startport
template_dir = basedir + "/template/"
temp_dir = basedir + "/temp/"
static_dir = basedir + "/static/"
natural4_dir = temp_dir + "workdir"

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


# ################################################
#            SERVE (MOST) STATIC FILES
# ################################################
#  secondary handler serves .l4, .md, .hs, etc static files

@app.route("/workdir/<uuid>/<ssid>/<sid>/<channel>/<filename>")
def get_workdir_file(uuid, ssid, sid, channel, filename):
    print("get_workdir_file: handling request for %s/%s/%s/%s/%s" % (uuid, ssid, sid, channel, filename), file=sys.stderr)
    workdir_folder = temp_dir + "workdir/" + uuid + "/" + ssid + "/" + sid + "/" + channel
    if not os.path.exists(workdir_folder):
        print("get_workdir_file: unable to find workdir_folder " + workdir_folder, file=sys.stderr)
        return

    if not os.path.isfile(workdir_folder + "/" + filename):
        print("get_workdir_file: unable to find file %s/%s" % (workdir_folder, filename), file=sys.stderr)
        return

    (fn, ext) = os.path.splitext(filename)
    if ext in {".l4", ".epilog", ".purs", ".org", ".hs", ".ts", ".natural4"}:
        print("get_workdir_file: returning text/plain %s/%s" % (workdir_folder, filename), file=sys.stderr)
        return send_file(workdir_folder + "/" + filename, mimetype="text/plain")
    else:
        print("get_workdir_file: returning %s/%s" % (workdir_folder, filename), file=sys.stderr)
        return send_file(workdir_folder + "/" + filename)


# ################################################
#            SERVE SVG STATIC FILES
# ################################################
# this is handled a little differently because
# the directory structure for SVG output is a bit
# more complicated than for the other outputs.
# There is a LATEST directory instead of a LATEST file
# so the directory path is a little bit different.

@app.route("/aasvg/<uuid>/<ssid>/<sid>/<image>")
def show_aasvg_image(uuid, ssid, sid, image):
    print("show_aasvg_image: handling request for /aasvg/ url", file=sys.stderr)
    aasvg_folder = temp_dir + "workdir/" + uuid + "/" + ssid + "/" + sid + "/aasvg/LATEST/"
    image_path = aasvg_folder + image
    print("show_aasvg_image: sending path " + image_path, file=sys.stderr)
    return send_file(image_path)


maude_main_file = Path('natural4_maude') / 'main.maude'
maude_main_mod = maude_vis.init_maude_n_load_main_file(maude_main_file)

# ################################################
#                      main
#      HANDLE POSTED CSV, RUN NATURAL4 & ETC
# ################################################
# This is the function that does all the heavy lifting.

@app.route("/post", methods=['GET', 'POST'])
async def process_csv():
  start_time = datetime.datetime.now()
  print("hello.py processCsv() starting at ", start_time, file=sys.stderr)

  data = request.form.to_dict()

  response = {}

  uuid = data['uuid']
  spreadsheet_id = data['spreadsheet_id']
  sheet_id = data['sheet_id']
  target_folder = natural4_dir + "/" + uuid + "/" + spreadsheet_id + "/" + sheet_id + "/"
  print(target_folder)
  time_now = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S.%fZ")
  target_file = time_now + ".csv"
  target_path = target_folder + target_file
  # if not os.path.exists(target_folder):
  Path(target_folder).mkdir(parents=True, exist_ok=True)

  with open(target_path, "w") as fout:
    fout.write(data['csvString'])

  # target_path is for CSV data

# ---------------------------------------------
# call natural4-exe, wait for it to complete. see SECOND RUN below.
# ---------------------------------------------

  # one can leave out the markdown by adding the --tomd option
  # one can leave out the ASP by adding the --toasp option
  create_files = natural4_exe + " --tomd --toasp --workdir=" + natural4_dir + " --uuiddir=" + uuid + "/" + spreadsheet_id + "/" + sheet_id + " " + target_path
  print("hello.py main: calling natural4-exe (%s)" % (natural4_exe), file=sys.stderr)
  print("hello.py main: %s" % (create_files), file=sys.stderr)
  nl4exe = subprocess.run([create_files], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  print("hello.py main: back from fast natural4-exe (took", datetime.datetime.now() - start_time, ")", file=sys.stderr)
  print("hello.py main: natural4-exe stdout length = %d" % len(nl4exe.stdout.decode('utf-8')), file=sys.stderr)
  print("hello.py main: natural4-exe stderr length = %d" % len(nl4exe.stderr.decode('utf-8')), file=sys.stderr)

  if len(nl4exe.stderr.decode('utf-8')) < 2000:
      print(nl4exe.stderr.decode('utf-8'))
  nl4_out = nl4exe.stdout.decode('utf-8')
  with open(target_folder + time_now + ".err", "w") as fout:
      fout.write(nl4exe.stderr.decode('utf-8'))
  with open(target_folder + time_now + ".out", "w") as fout:
      fout.write(nl4exe.stdout.decode('utf-8'))

  response['nl4_stderr'] = nl4exe.stderr.decode('utf-8')[:20000]
  response['nl4_stdout'] = nl4exe.stdout.decode('utf-8')[:20000]

  # ---------------------------------------------
  # postprocessing: for petri nets: turn the DOT files into PNGs
  # ---------------------------------------------

  uuid_ss_folder = temp_dir + "workdir/" + uuid + "/" + spreadsheet_id + "/" + sheet_id
  petri_folder = uuid_ss_folder + "/petri/"
  dot_path = petri_folder + "LATEST.dot"
  (timestamp, ext) = os.path.splitext(os.readlink(dot_path))

  if not os.path.exists(petri_folder):
      print("expected to find petri_folder %s but it's not there!" % (petri_folder), file=sys.stderr)
  else:
      petri_path_svg = petri_folder + timestamp + ".svg"
      petri_path_png = petri_folder + timestamp + ".png"
      small_petri_path = petri_folder + timestamp + "-small.png"
      print("hello.py main: running: dot -Tpng -Gdpi=150 " + dot_path + " -o " + petri_path_png + " &", file=sys.stderr)
      os.system("dot -Tpng -Gdpi=72  " + dot_path + " -o " + small_petri_path + " &")
      os.system("dot -Tpng -Gdpi=150 " + dot_path + " -o " + petri_path_png + " &")
      os.system("dot -Tsvg           " + dot_path + " -o " + petri_path_svg + " &")
      try:
          if os.path.isfile(petri_folder + "LATEST.svg"):       os.unlink(petri_folder + "LATEST.svg")
          if os.path.isfile(petri_folder + "LATEST.png"):       os.unlink(petri_folder + "LATEST.png")
          if os.path.isfile(petri_folder + "LATEST-small.png"): os.unlink(petri_folder + "LATEST-small.png")
          os.symlink(os.path.basename(petri_path_svg), petri_folder + "LATEST.svg")
          os.symlink(os.path.basename(petri_path_png), petri_folder + "LATEST.png")
          os.symlink(os.path.basename(small_petri_path), petri_folder + "LATEST-small.png")
      except Exception as e:
          print("hello.py main: got some kind of OS error to do with the unlinking and the symlinking",
                file=sys.stderr)
          print("hello.py main: %s" % (e), file=sys.stderr)

  # ---------------------------------------------
  # postprocessing: for the babyl4 downstream transpilations
  # - call l4 epilog corel4/LATEST.l4
  # ---------------------------------------------

  core_l4_path = uuid_ss_folder + "/corel4/LATEST.l4"
  epilog_path = uuid_ss_folder + "/epilog"
  Path(epilog_path).mkdir(parents=True, exist_ok=True)
  epilog_file = epilog_path + "/" + time_now + ".epilog"

  print("hello.py main: running: l4 epilog " + core_l4_path + " > " + epilog_file, "&", file=sys.stderr)
  os.system("l4 epilog " + core_l4_path + " > " + epilog_file + " &")
  if os.path.isfile(epilog_path + "/LATEST.epilog"): os.unlink(epilog_path + "/LATEST.epilog")
  os.symlink(time_now + ".epilog", epilog_path + "/LATEST.epilog")

# ---------------------------------------------
# postprocessing: (re-)launch the vue web server
# - call v8k up
# ---------------------------------------------

  v8kargs = ["python", v8k_path,
              "--workdir=" + v8k_workdir,
              "up",
              "--uuid=" + uuid,
              "--ssid=" + spreadsheet_id,
              "--sheetid=" + sheet_id,
              "--startport=" + v8k_startport,
              uuid_ss_folder + "/purs/LATEST.purs"]

  print("hello.py main: calling %s" % (" ".join(v8kargs)), file=sys.stderr)
  os.system(" ".join(v8kargs) + "> " + uuid_ss_folder + "/v8k.out")
  print("hello.py main: v8k up returned", file=sys.stderr)
  with open(uuid_ss_folder + "/v8k.out", "r") as read_file:
      v8k_out = read_file.readline();
  print("v8k.out: %s" % (v8k_out), file=sys.stderr)

  if re.match(r':\d+', v8k_out):  # we got back the expected :8001/uuid/ssid/sid whatever from the v8k call
      v8k_url = v8k_out.strip()
      print("v8k up succeeded with: " + v8k_url, file=sys.stderr)
      response['v8k_url'] = v8k_url
  else:
      response['v8k_url'] = None

# ---------------------------------------------
# load in the aasvg index HTML to pass back to sidebar
# ---------------------------------------------

  with open(uuid_ss_folder + "/aasvg/LATEST/index.html", "r") as read_file:
      response['aasvg_index'] = read_file.read()

# ---------------------------------------------
# construct other response elements and log run-timings.
# ---------------------------------------------

  response['timestamp'] = timestamp

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
    # print("hello.py processCsv parent returning at", datetime.datetime.now(), "(total", datetime.datetime.now() - start_time, ")", file=sys.stderr)
    print("hello.py processCsv parent returning at ", datetime.datetime.now(), "(total",
          datetime.datetime.now() - start_time, ")", file=sys.stderr)
    # print(json.dumps(response), file=sys.stderr)

    return json.dumps(response)
  else:  # in the child
    print("hello.py processCsv: fork(child): continuing to run", file=sys.stderr)

    create_files = natural4_exe + " --only tomd --workdir=" + natural4_dir + " --uuiddir=" + uuid + "/" + spreadsheet_id + "/" + sheet_id + " " + target_path
    print("hello.py child: calling natural4-exe (%s) (slowly) for tomd" % (natural4_exe), file=sys.stderr)
    print("hello.py child: %s" % (create_files), file=sys.stderr)
    nl4exe = subprocess.run([create_files], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("hello.py child: back from slow natural4-exe 1 (took", datetime.datetime.now() - start_time, ")",
          file=sys.stderr)
    print("hello.py child: natural4-exe stdout length = %d" % len(nl4exe.stdout.decode('utf-8')), file=sys.stderr)
    print("hello.py child: natural4-exe stderr length = %d" % len(nl4exe.stderr.decode('utf-8')), file=sys.stderr)

    print("hello.py child: returning at", datetime.datetime.now(), "(total", datetime.datetime.now() - start_time,
          ")", file=sys.stderr)

    # ---------------------------------------------
    # Postprocessing:
    # Turn textual natural4 files generated by Maude transpiler into interactive
    # HTML visualizations of the state space.
    # ---------------------------------------------
    maude_path = Path(uuid_ss_folder) / 'maude'
    maude_path.mkdir(parents=True, exist_ok=True)
    natural4_file = maude_path / 'LATEST.natural4'
    natural4_rules = None
    with open(natural4_file) as f:
        natural4_rules = f.read()

  # We don't proceed with post processing if the natural4 file is empty or
  # contains only whitespaces.
  if natural4_rules.strip():
    # Transform the set of rules into the initial configuration of the
    # transition system.
    config = maude_vis.natural4_rules_to_config(
      maude_main_mod, natural4_rules
    )
    if config:
      # Here we use asyncio to generate the state space graph and find a
      # race condition trace in parallel, with a timeout of 30s.
      async with asyncio.timeout(30):
        await asyncio.gather(
          # Generate state space graph.
          # graph.expand() in FailFreeGraph may take forever because the state space
          # may be infinite.
          asyncio.to_thread(
            maude_vis.config_to_html_file,
            maude_main_mod, config, 'all *',
            maude_path / 'LATEST_state_space.html'
          ),

          # Find a trace with race conditions and generate a graph.
          asyncio.to_thread(
            maude_vis.natural4_rules_to_race_cond_htmls,
            maude_main_mod,
            maude_path / 'LATEST_race_cond.html',
            natural4_rules
          )
        )

      # this return shouldn't mean anything because we're in the child, but gunicorn may somehow pick it up?
      return json.dumps(response)

  # ---------------------------------------------
  # return to sidebar caller
  # ---------------------------------------------

# ################################################
# run when not launched via gunicorn
# ################################################

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True, processes=6)
