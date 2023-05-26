#
# this file is intended to be customized for each installation; change it as you wish
#

# pythonpath = "/home/mengwong/src/smucclaw/gsheet/pyrest/lib/python3.8/site-packages/"
raw_env = ["basedir="       + ".",
           # "V8K_WORKDIR="   + "/home/mengwong/wow/much",
           "V8K_WORKDIR="   + "/home/joe/v8k_workdir",
           "v8k_startport=" + "8201",
           "v8k_path="      + "/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k",
           # "maudedir="      + ""
           ]
bind     = "0.0.0.0:8200"

certfile   = "/etc/letsencrypt/live/cclaw.legalese.com/cert.pem"
keyfile    = "/etc/letsencrypt/live/cclaw.legalese.com/privkey.pem"

preload = True
accesslog = "access_log"
workers  = 3
