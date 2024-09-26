#
# this file is intended to be customized for each installation; change it as you wish
#

bindport = 8300

pythonpath = ""
raw_env = [
    "basedir=" + ".",
    "V8K_WORKDIR=" + "/home/maxloo/v8kworkdir",
    "v8k_startport=" + str(bindport + 1),
    "v8k_path=" + "/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k",
    "natural4_exe=" + "natural4-exe",
    "CCLAW_HTTPS=" + "true, set in gunicorn.conf.py so production supports https",
    # for details on CCLAW_HTTPS, see vue-pure-pdpa/vue.config.js
]
bind = "0.0.0.0:" + str(bindport)

certfile = "/etc/letsencrypt/live/cclaw.legalese.com/cert.pem"
keyfile = "/etc/letsencrypt/live/cclaw.legalese.com/privkey.pem"

preload = True
accesslog = "access_log"
workers = 3
