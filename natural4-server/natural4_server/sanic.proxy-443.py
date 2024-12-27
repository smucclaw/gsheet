from io import StringIO
from dotenv import load_dotenv
from hello import app

# Define and load environment variables.
raw_env: str = """
basedir=.
"""

load_dotenv(stream=StringIO(raw_env))

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8400,
        fast=True,
        access_log=False,
        #    ssl = '/etc/letsencrypt/live/cclaw.legalese.com/'
    )
