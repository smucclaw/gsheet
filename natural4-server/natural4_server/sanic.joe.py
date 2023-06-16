from io import StringIO
from dotenv import load_dotenv

# Define and load environment variables.
raw_env: str = '''
basedir=.
V8K_WORKDIR=/home/joe/v8k_workdir
v8k_startport=8201
v8k_path=/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k
'''

load_dotenv(stream = StringIO(raw_env))

from hello import app

ssl: dict[str, str] = {
  'cert': '/etc/letsencrypt/live/cclaw.legalese.com/cert.pem',
  'key': '/etc/letsencrypt/live/cclaw.legalese.com/privkey.pem'
}

if __name__ == '__main__':
  app.run(
    host = '0.0.0.0', port = 8200,
    fast = True,
    access_log = False,
    ssl = ssl
  )