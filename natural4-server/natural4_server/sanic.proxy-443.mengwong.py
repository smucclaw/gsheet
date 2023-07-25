from io import StringIO
from dotenv import load_dotenv
from hello import app

# Define and load environment variables.
raw_env: str = '''
basedir=.
V8K_WORKDIR=/home/mengwong/v8kworkdir-8090
v8k_startport=8091
'''

load_dotenv(stream=StringIO(raw_env))

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8090,
        fast=True,
        access_log=False,
        #    ssl = '/etc/letsencrypt/live/cclaw.legalese.com/'
    )
