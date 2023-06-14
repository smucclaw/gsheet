#
# 8090 is a dev unstable port running the latest build on main
# it was previously on 8081 but that has been deprecated
#

bindport=8090

raw_env = ["basedir="       + ".",
           "V8K_WORKDIR="   + "/home/mengwong/v8kworkdir",
           "v8k_startport=" + str(bindport + 1),
           "v8k_path="      + "/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k",
           "natural4_exe="  + "natural4-unstable",
           "CCLAW_HTTPS="   + "true, set in gunicorn.conf.py so production supports https"
           ]
bind     = "0.0.0.0:" + str(bindport)

certfile   = "/etc/letsencrypt/live/cclaw.legalese.com/cert.pem"
keyfile    = "/etc/letsencrypt/live/cclaw.legalese.com/privkey.pem"

preload = True
accesslog = "access_log"
workers  = 3

