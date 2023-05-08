#
# 8090 is a dev unstable port running the latest build on main
# it was previously on 8081 but that has been deprecated
#

bindport=8090

pythonpath = "/home/mengwong/src/smucclaw/gsheet/pyrest/lib/python3.8/site-packages/"
raw_env = ["basedir="       + ".",
           "V8K_WORKDIR="   + "/home/mengwong/wow/much",
           "v8k_startport=" + str(bindport + 1),
           "v8k_path="      + "/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k",
           "natural4_exe="  + "natural4-unstable"
           ]
bind     = "0.0.0.0:" + str(bindport)

certfile   = "/etc/letsencrypt/live/cclaw.legalese.com/cert.pem"
keyfile    = "/etc/letsencrypt/live/cclaw.legalese.com/privkey.pem"

preload = True
accesslog = "access_log"
workers  = 3

