#
# 
#

pythonpath = "/home/mengwong/src/smucclaw/gsheet/pyrest/lib/python3.8/site-packages/"
raw_env = ["basedir="       + ".",
           "V8K_WORKDIR="   + "/home/mengwong/wow/much",
           "v8k_startport=" + "8092",
           "v8k_path="      + "/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k"
           ]
bind     = "0.0.0.0:8081"

certfile   = "/etc/letsencrypt/live/cclaw.legalese.com/cert.pem"
keyfile    = "/etc/letsencrypt/live/cclaw.legalese.com/privkey.pem"

preload = True
accesslog = "access_log"
workers  = 3

