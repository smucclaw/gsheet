from flask import Flask, request, send_from_directory, render_template, send_file
import sys, string, os, datetime, glob, shutil, subprocess, re
from pathlib import Path

template_dir = "/home/mengwong/pyrest/template/"
temp_dir = "/home/mengwong/pyrest/temp/"
static_dir = "/home/mengwong/pyrest/static/"
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

@app.route("/corel4/<uuid>/<ssid>/<sid>")
def getCorel4File(uuid, ssid, sid):
  textStr = ""
  corel4Folder = temp_dir + "workdir/" + uuid + "/" + ssid + "/" + sid + "/corel4/"
  with open(corel4Folder + "LATEST.l4", "r") as fin:
    for line in fin.readlines():
      textStr = textStr + line
  return render_template("corel4.html", data=textStr)

@app.route("/petri/<uuid>/<ssid>/<sid>")
def getPetriFile(uuid, ssid, sid):
  petriFolder = temp_dir + "workdir/" + uuid + "/" + ssid + "/" + sid + "/petri/"
  dotPath = petriFolder + "LATEST.dot"
  if not os.path.exists(petriFolder):
    Path(petriFolder).mkdir(parents=True, exist_ok=True)
  petriPath = petriFolder + "LATEST.png"
  return render_template("petri.html",
                         uuid = uuid,
                         ssid = ssid,
                         sid  = sid )

# secondary handler used by
#######  the petri template img src ... and others

# [TODO] we probably want to also just make the filename fully explicit to defeat caching

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
  if ext == ".l4":
    print("getWorkdirFile: returning text/plain %s/%s" % (workdirFolder, filename), file=sys.stderr)
    return send_file(workdirFolder + "/" + filename, mimetype="text/plain")
  else:
    print("getWorkdirFile: returning %s/%s" % (workdirFolder, filename), file=sys.stderr)
    return send_file(workdirFolder + "/" + filename)

@app.route("/aasvg/<uuid>/<ssid>/<sid>/<image>")
def showAasvgImage(uuid, ssid, sid, image):
  aasvgFolder = temp_dir + "workdir/" + uuid + "/" + ssid + "/" + sid + "/aasvg/LATEST/"
  imagePath = aasvgFolder + image
  cutPathToStaticImage = "workdir/" + uuid + "/" + ssid + "/" + sid + "/" + image
  newImagePath = static_dir + cutPathToStaticImage
  newImageFolderPath = static_dir + "workdir/" + uuid + "/" + ssid + "/" + sid + "/"
  Path(newImageFolderPath).mkdir(parents=True, exist_ok=True)
  shutil.copy(imagePath, newImagePath)
  return render_template("aasvg.html", image = cutPathToStaticImage, image_title = image[:-4])

@app.route("/aasvg/<uuid>/<ssid>/<sid>")
def getAasvgHtml(uuid, ssid, sid):
  aasvgFolder = temp_dir + "workdir/" + uuid + "/" + ssid + "/" + sid + "/aasvg/LATEST/"
  aasvgHtml = aasvgFolder + "index.html"
  f = []
  textStr = ""
  for (dirpath, dirnames, filenames) in os.walk(aasvgFolder):
    f.extend(filenames)
    break
  print(f)
  cutPathToIndexDir = "aasvgindexdir/" + uuid + "/" + ssid + "/" + sid + "/"
  Path(template_dir + cutPathToIndexDir).mkdir(parents=True, exist_ok=True)
  cutPathToIndex = cutPathToIndexDir + "aasvg_index.html"
  for fileName in f:
    if (fileName != "index.html") and (fileName[-3:] == 'svg'):
      textStr = textStr + '<li> <a href="/aasvg/' + uuid + '/' + ssid + '/' + sid + '/' + fileName + '">' + fileName[:-4] + '</a></li>\n'
  with open(aasvgHtml, "w") as fout:
    fout.write(textStr)
  shutil.copy(aasvgHtml, template_dir + cutPathToIndex)
  # return render_template(cutPathToIndex)
  return textStr

@app.route("/post", methods=['GET', 'POST'])
def processCsv():
  data = request.form.to_dict()

  uuid = data['uuid']
  spreadsheetId = data['spreadsheetId']
  sheetId = data['sheetId']
  targetFolder = "/home/mengwong/pyrest/temp/workdir/"+uuid+"/"+spreadsheetId+"/"+sheetId+"/"
  print(targetFolder)
  targetFile = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S.%fZ") + ".csv"
  targetPath = targetFolder + targetFile
  # if not os.path.exists(targetFolder):
  Path(targetFolder).mkdir(parents=True, exist_ok=True)

  with open(targetPath, "w") as fout:
    fout.write(data['csvString'])

  # targetPath is for CSV data
  createFiles = "natural4-exe --workdir=/home/mengwong/pyrest/temp/workdir --uuiddir=" + uuid + "/" + spreadsheetId + "/" + sheetId + " " + targetPath
  # createFiles = "natural4-exe --workdir=/home/mengwong/pyrest/temp/workdir --uuiddir=" + uuid + " --topetri=petri --tojson=json --toaasvg=aasvg --tonative=native --tocorel4=corel4 --tocheckl=checklist  --tots=typescript " + targetPath
  print("hello.py main: calling natural4-exe", file=sys.stderr)
  nl4exe = subprocess.run([createFiles], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  print("hello.py main: back from natural4-exe", file=sys.stderr)
  print("hello.py main: natural4-exe stdout length = ", len(nl4exe.stdout.decode('utf-8')))
  print("hello.py main: natural4-exe stderr length = ", len(nl4exe.stderr.decode('utf-8')))
  if len(nl4exe.stderr.decode('utf-8')) < 2000:
    print (nl4exe.stderr.decode('utf-8'))
  nl4_out = nl4exe.stdout.decode('utf-8')
    
  # 
  # postprocessing after running natural4-exe:
  #   postprocessing for petri nets:
  #     turn the DOT files into PNGs

  uuidssfolder = temp_dir + "workdir/" + uuid + "/" + spreadsheetId + "/" + sheetId
  petriFolder = uuidssfolder + "/petri/"
  dotPath = petriFolder + "LATEST.dot"
  (timestamp,ext) = os.path.splitext(os.readlink(dotPath));

  if not os.path.exists(petriFolder):
    print("expected to find petriFolder %s but it's not there!" % (petriFolder), file=sys.stderr);
  else:
    petriPath = petriFolder + timestamp + ".png"
    smallPetriPath = petriFolder + timestamp + "-small.png"
    print("hello.py main: running: dot -Tpng -Gdpi=150 " + dotPath + " -o " + petriPath + " &", file=sys.stderr)
    os.system("dot -Tpng -Gdpi=24  " + dotPath + " -o " + smallPetriPath + " &")
    os.system("dot -Tpng -Gdpi=150 " + dotPath + " -o " + petriPath + " &")
    try:
      if os.path.isfile(petriFolder + "LATEST.png"):       os.unlink(                 petriFolder + "LATEST.png")
      if os.path.isfile(petriFolder + "LATEST-small.png"): os.unlink(                 petriFolder + "LATEST-small.png")
      os.symlink(os.path.basename(petriPath),      petriFolder + "LATEST.png")
      os.symlink(os.path.basename(smallPetriPath), petriFolder + "LATEST-small.png")
    except Exception as e:
      print("hello.py main: got some kind of OS error to do with the unlinking and the symlinking", file=sys.stderr);
      print("hello.py main: %s" % (e), file=sys.stderr);
    
    #   postprocessing for the vue web server
    #     call v8k up

    v8kargs = ["/home/mengwong/pyrest/bin/python", "/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k", "up",
               "--uuid="    + uuid,
               "--ssid="    + spreadsheetId,
               "--sheetid=" + sheetId,
               uuidssfolder + "/purs/LATEST.purs"]
    
    print("hello.py main: calling %s" % (" ".join(v8kargs)), file=sys.stderr)
# v8k = subprocess.run(v8kargs,
#                            stdout=subprocess.PIPE,
#                            stderr=subprocess.PIPE
#    )
    os.system(" ".join(v8kargs) + "> " + uuidssfolder + "v8k.out");
    print("hello.py main: v8k up returned", file=sys.stderr)
    with open(uuidssfolder + "v8k.out", "r") as read_file:
      v8k_out = read_file.readline();
    print("v8k.out: %s" % (v8k_out), file=sys.stderr)

    # v8k_out = v8k.stdout.decode('utf-8')
    
    if re.match(r':\d+', v8k_out): # we got back the expected :8001/uuid/ssid/sid whatever from the v8k call
      v8k_url = v8k_out
      print("v8k up succeeded with: " + v8k_url, file=sys.stderr)
    else:
      v8k_url = ""
#      v8k_error = v8k.stderr.decode('utf-8')
#      print("hello.py main: v8k up stderr: " + v8k_error,                  file=sys.stderr)
#      print("hello.py main: v8k up stdout: " + v8k.stdout.decode('utf-8'), file=sys.stderr)
      
  # [TODO]: return a JSON object instead from which the sidebar can construct prettier links and thumbnails
  
  textStr = ("v8k_url=" + v8k_url +
             "\ntimestamp=" + timestamp +
             "\n\n" + nl4_out)
  print("hello.py main: returning", file=sys.stderr)
  return textStr

@app.route("/you/<name>")
def user(name):
  return """
      <!DOCTYPE html>
      <html>
      <head><title>Hello</title></head>
      <body><h1>Hello, {name}</h1></body>
      </html>
      """.format(name=name), 200

@app.route("/")
def hello():
  return "Hello World!"

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=False, threaded=True, processes=6)


