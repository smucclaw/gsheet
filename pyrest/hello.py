
# ################################################
#               ONLINE DOCUMENTATION
# ################################################
# please see https://docs.google.com/document/d/1EvyiQhSgapumBRt9UloRpwiRcgVhF-m65FVdAz3chfs/edit#
# software version: 1.1.3

# ################################################
#          INVOCATION AND CONFIGURATION
# ################################################
# There is no #! line because we are run out of gunicorn.

from flask import Flask, request, send_from_directory, render_template, send_file
import sys, string, os, datetime, glob, shutil, subprocess, re, json
from pathlib import Path
import datetime

if "basedir"       in os.environ: basedir       = os.environ["basedir"]
if "V8K_WORKDIR"   in os.environ: v8k_workdir   = os.environ["V8K_WORKDIR"]
if "v8k_startport" in os.environ: v8k_startport = os.environ["v8k_startport"]
if "v8k_path"      in os.environ: v8k_path      = os.environ["v8k_path"]

# see gunicorn.conf.py for basedir, workdir, startport
template_dir = basedir + "/template/"
temp_dir     = basedir + "/temp/"
static_dir   = basedir + "/static/"
natural4_dir = temp_dir + "workdir"

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


# ################################################
#            SERVE (MOST) STATIC FILES
# ################################################
#  secondary handler serves .l4, .md, .hs, etc static files

@app.route("/workdir/<uuid>/<ssid>/<sid>/<channel>/<filename>")
def getWorkdirFile(uuid, ssid, sid, channel, filename):
  workdirFolder = temp_dir + "workdir/" + uuid + "/" + ssid + "/" + sid + "/" + channel
  if not os.path.exists(workdirFolder):
    print("getWorkdirFile: unable to find workdirFolder " + workdirFolder, file=sys.stderr)
    return;
  if not os.path.isfile(workdirFolder + "/" + filename):
    print("getWorkdirFile: unable to find file %s/%s"  % (workdirFolder, filename), file=sys.stderr)
    return;
  (fn,ext) = os.path.splitext(filename)
  if (ext == ".l4"
      or ext == ".epilog"
      or ext == ".purs"
      or ext == ".org"
      or ext == ".hs"
      or ext == ".ts"
      ):

    print("getWorkdirFile: returning text/plain %s/%s" % (workdirFolder, filename), file=sys.stderr)
    return send_file(workdirFolder + "/" + filename, mimetype="text/plain")
  else:
    print("getWorkdirFile: returning %s/%s" % (workdirFolder, filename), file=sys.stderr)
    return send_file(workdirFolder + "/" + filename)



# ################################################
#            SERVE SVG STATIC FILES
# ################################################
# this is handled a little differently because
# the directory structure for SVG output is a bit
# more complicated than for the other outputs.
# There is a LATEST directory instead of a LATEST file
# so the directory path is a little bit different.

@app.route("/aasvg/<uuid>/<ssid>/<sid>/<image>")
def showAasvgImage(uuid, ssid, sid, image):
  print("showAasvgImage: handling /aasvg/ url", file=sys.stderr);
  aasvgFolder = temp_dir + "workdir/" + uuid + "/" + ssid + "/" + sid + "/aasvg/LATEST/"
  imagePath = aasvgFolder + image
  print("showAasvgImage: sending path " + imagePath, file=sys.stderr)
  return send_file(imagePath)




# ################################################
#                      main
#      HANDLE POSTED CSV, RUN NATURAL4 & ETC
# ################################################
# This is the function that does all the heavy lifting.

@app.route("/post", methods=['GET', 'POST'])
def processCsv():
  startTime = datetime.datetime.now()
  print("hello.py processCsv() starting at ", startTime, file=sys.stderr)

  data = request.form.to_dict()

  response = {}

  uuid = data['uuid']
  spreadsheetId = data['spreadsheetId']
  sheetId = data['sheetId']
  targetFolder = natural4_dir + "/"+uuid+"/"+spreadsheetId+"/"+sheetId+"/"
  print(targetFolder)
  timeNow = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S.%fZ")
  targetFile = timeNow + ".csv"
  targetPath = targetFolder + targetFile
  # if not os.path.exists(targetFolder):
  Path(targetFolder).mkdir(parents=True, exist_ok=True)

  with open(targetPath, "w") as fout:
    fout.write(data['csvString'])

  # targetPath is for CSV data

  # ---------------------------------------------
  # call natural4-exe, wait for it to complete
  # ---------------------------------------------

  # one can leave out the markdown by adding the --tomd option
  # one can leave out the ASP by adding the --toasp option
  createFiles = "natural4-exe --toasp --workdir=" + natural4_dir + " --uuiddir=" + uuid + "/" + spreadsheetId + "/" + sheetId + " " + targetPath
  print("hello.py main: calling natural4-exe", file=sys.stderr)
  print("hello.py main: %s" % (createFiles), file=sys.stderr)
  nl4exe = subprocess.run([createFiles], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  print("hello.py main: back from natural4-exe (took", datetime.datetime.now() - startTime, ")", file=sys.stderr)
  print("hello.py main: natural4-exe stdout length = %d" % len(nl4exe.stdout.decode('utf-8')), file=sys.stderr)
  print("hello.py main: natural4-exe stderr length = %d" % len(nl4exe.stderr.decode('utf-8')), file=sys.stderr)
   
  if len(nl4exe.stderr.decode('utf-8')) < 2000:
    print (nl4exe.stderr.decode('utf-8'))
  nl4_out = nl4exe.stdout.decode('utf-8')

  response['nl4_stderr'] = nl4exe.stderr.decode('utf-8')[:20000]
  response['nl4_stdout'] = nl4exe.stdout.decode('utf-8')[:20000]

  # ---------------------------------------------
  # postprocessing: for petri nets: turn the DOT files into PNGs
  # ---------------------------------------------

  uuidssfolder = temp_dir + "workdir/" + uuid + "/" + spreadsheetId + "/" + sheetId
  petriFolder = uuidssfolder + "/petri/"
  dotPath = petriFolder + "LATEST.dot"
  (timestamp,ext) = os.path.splitext(os.readlink(dotPath));

  if not os.path.exists(petriFolder):
    print("expected to find petriFolder %s but it's not there!" % (petriFolder), file=sys.stderr);
  else:
    petriPathsvg = petriFolder + timestamp + ".svg"
    petriPathpng = petriFolder + timestamp + ".png"
    smallPetriPath = petriFolder + timestamp + "-small.png"
    print("hello.py main: running: dot -Tpng -Gdpi=150 " + dotPath + " -o " + petriPath + " &", file=sys.stderr)
    os.system("dot -Tpng -Gdpi=72  " + dotPath + " -o " + smallPetriPath + " &")
    os.system("dot -Tpng -Gdpi=150 " + dotPath + " -o " + petriPathpng + " &")
    os.system("dot -Tsvg           " + dotPath + " -o " + petriPathsvg + " &")
    try:
      if os.path.isfile(petriFolder + "LATEST.svg"):       os.unlink(                 petriFolder + "LATEST.svg")
      if os.path.isfile(petriFolder + "LATEST.png"):       os.unlink(                 petriFolder + "LATEST.png")
      if os.path.isfile(petriFolder + "LATEST-small.png"): os.unlink(                 petriFolder + "LATEST-small.png")
      os.symlink(os.path.basename(petriPathsvg),   petriFolder + "LATEST.svg")
      os.symlink(os.path.basename(petriPathpng),   petriFolder + "LATEST.png")
      os.symlink(os.path.basename(smallPetriPath), petriFolder + "LATEST-small.png")
    except Exception as e:
      print("hello.py main: got some kind of OS error to do with the unlinking and the symlinking", file=sys.stderr);
      print("hello.py main: %s" % (e), file=sys.stderr);
    
  # ---------------------------------------------
  # postprocessing: for the babyl4 downstream transpilations
  # - call l4 epilog corel4/LATEST.l4
  # ---------------------------------------------

  corel4Path = uuidssfolder + "/corel4/LATEST.l4"
  epilogPath = uuidssfolder + "/epilog"
  Path(epilogPath).mkdir(parents=True, exist_ok=True)
  epilogFile = epilogPath + "/" + timeNow + ".epilog"

  print("hello.py main: running: l4 epilog " + corel4Path + " > " + epilogFile, "&", file=sys.stderr)
  os.system("l4 epilog " + corel4Path + " > " + epilogFile + " &")
  if os.path.isfile(epilogPath + "/LATEST.epilog"): os.unlink( epilogPath + "/LATEST.epilog")
  os.symlink(timeNow + ".epilog", epilogPath + "/LATEST.epilog")

  # ---------------------------------------------
  # postprocessing: (re-)launch the vue web server
  # - call v8k up
  # ---------------------------------------------

  v8kargs = ["python", v8k_path,
             "--workdir=" + v8k_workdir,
             "up",
             "--uuid="    + uuid,
             "--ssid="    + spreadsheetId,
             "--sheetid=" + sheetId,
             "--startport=" + v8k_startport,
             uuidssfolder + "/purs/LATEST.purs"]
  
  print("hello.py main: calling %s" % (" ".join(v8kargs)), file=sys.stderr)
  os.system(" ".join(v8kargs) + "> " + uuidssfolder + "/v8k.out");
  print("hello.py main: v8k up returned", file=sys.stderr)
  with open(uuidssfolder + "/v8k.out", "r") as read_file:
    v8k_out = read_file.readline();
  print("v8k.out: %s" % (v8k_out), file=sys.stderr)

  if re.match(r':\d+', v8k_out): # we got back the expected :8001/uuid/ssid/sid whatever from the v8k call
    v8k_url = v8k_out.strip()
    print("v8k up succeeded with: " + v8k_url, file=sys.stderr)
    response['v8k_url'] = v8k_url
  else:
    v8k_url = ""
    response['v8k_url'] = None
    #      v8k_error = v8k.stderr.decode('utf-8')
    #      print("hello.py main: v8k up stderr: " + v8k_error,                  file=sys.stderr)
    #      print("hello.py main: v8k up stdout: " + v8k.stdout.decode('utf-8'), file=sys.stderr)
    
  # ---------------------------------------------
  # load in the aasvg index HTML to pass back to sidebar
  # ---------------------------------------------

  with open(uuidssfolder + "/aasvg/LATEST/index.html", "r") as read_file:
    response['aasvg_index'] = read_file.read();

  # ---------------------------------------------
  # construct other response elements and log run-timings.
  # ---------------------------------------------

  response['timestamp'] = timestamp;
  
  endTime = datetime.datetime.now()
  elapsedT = endTime.timestamp() - startTime.timestamp()

  print("hello.py processCsv returning at", endTime, "(total", elapsedT, ")", file=sys.stderr)

  # ---------------------------------------------
  # return to sidebar caller
  # ---------------------------------------------

  # print(json.dumps(response), file=sys.stderr)
  return json.dumps(response)

# ################################################
# run when not launched via gunicorn
# ################################################

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=False, threaded=True, processes=6)


