#!/bin/sh

virtualenv pyrest/
cd pyrest
source bin/activate

export FLASK_APP=hello.py
export FLASK_DEBUG=1
export V8K_WORKDIR=/home/mengwong/wow/much
# flask run --host=0.0.0.0 --port=8080

# python3 hello.py

gunicorn --bind 0.0.0.0:8080 wsgi:app --pythonpath /home/mengwong/pyrest/lib/python3.8/site-packages/

