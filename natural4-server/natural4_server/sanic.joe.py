from io import StringIO

from dotenv import load_dotenv

from hello import app

raw_env: str = '''
basedir=.
V8K_WORKDIR=/home/joe/v8k_workdir
v8k_startport=8201
v8k_path=/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k
'''

ssl: dict[str, str] = {
  'cert': '/etc/letsencrypt/live/cclaw.legalese.com/cert.pem',
  'key': '/etc/letsencrypt/live/cclaw.legalese.com/privkey.pem'
}

load_dotenv(stream = StringIO(raw_env))

if __name__ == '__main__':
  app.run(
    host = '0.0.0.0', port = 8200,
    fast = True,
    access_log = False,
    ssl = ssl
  )