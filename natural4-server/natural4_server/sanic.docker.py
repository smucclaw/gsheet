import os
from io import StringIO

from dotenv import load_dotenv
from hello import app

START_PORT = int(os.getenv("START_PORT"))

raw_env: str = f"""
basedir=.
v8k_startport={START_PORT + 1}
"""

load_dotenv(stream=StringIO(raw_env))

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=START_PORT,
        fast=True,
        access_log=False,
    )
