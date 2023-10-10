from io import StringIO
from dotenv import load_dotenv
from hello import app


# Define and load environment variables.
raw_env: str = '''
basedir=.
V8K_WORKDIR=/home/mengwong/v8kworkdir-8080
v8k_startport=8081
v8k_path=/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k
natural4_exe=natural4-unstable
CCLAW_HTTPS="true, set in sanic.*.py"
'''





load_dotenv(stream=StringIO(raw_env))


ssl: dict[str, str] = {
    'cert': '/etc/letsencrypt/live/dev.cclaw.legalese.com/cert.pem',
    'key': '/etc/letsencrypt/live/dev.cclaw.legalese.com/privkey.pem'
}

if __name__ == '__main__':
    app.run(
        host='0.0.0.0', port=8080,
        fast=True,
        access_log=False,
#        ssl=ssl
    )
