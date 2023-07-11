from io import StringIO
from dotenv import load_dotenv

# Define and load environment variables.
raw_env: str = '''
basedir=.
V8K_WORKDIR=/home/rkhafizov/v8kworkdir
v8k_startport=8401
'''

load_dotenv(stream = StringIO(raw_env))

from hello import app


if __name__ == '__main__':
  app.run(
    host = '0.0.0.0',
    port = 8400,
    fast = True,
    access_log = False,
#    ssl = '/etc/letsencrypt/live/cclaw.legalese.com/'
  )
