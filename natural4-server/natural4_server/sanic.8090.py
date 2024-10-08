from io import StringIO
from dotenv import load_dotenv

# Define and load environment variables.
raw_env: str = """
basedir=.
V8K_WORKDIR=/home/mengwong/v8kworkdir-8090
v8k_startport=8091
v8k_path=/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k
natural4_exe=natural4-unstable
CCLAW_HTTPS="true, set in sanic.*.py"
"""

load_dotenv(stream=StringIO(raw_env))

from hello import app

ssl: dict[str, str] = {
    "cert": "/etc/letsencrypt/live/cclaw.legalese.com/cert.pem",
    "key": "/etc/letsencrypt/live/cclaw.legalese.com/privkey.pem",
}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090, fast=True, access_log=False, ssl=ssl)
