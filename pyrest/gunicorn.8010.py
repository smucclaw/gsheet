#
# 8080 is the production port which "stable" spreadsheets will point to.
#

pythonpath = "/home/mengwong/src/smucclaw/gsheet/pyrest/lib/python3.8/site-packages/"
raw_env = ["basedir="       + ".",
           "V8K_WORKDIR="   + "/home/mengwong/wow/much",
           "v8k_startport=" + "8011",
           "v8k_path="      + "/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k",
           "natural4_exe="  + "natural4-noqns"
           ]
bind     = "0.0.0.0:8010"

certfile   = "/etc/letsencrypt/live/cclaw.legalese.com/cert.pem"
keyfile    = "/etc/letsencrypt/live/cclaw.legalese.com/privkey.pem"

preload = True
accesslog = "access_log"
workers  = 3

