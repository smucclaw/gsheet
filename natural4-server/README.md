# Installing the python stuff

There's a uv config that you can use.

To use this:

1.  Install `pyenv` if you want to be able to easily toggle between
    python versions, and follow the docs for how to use `pyenv` with
    `uv`. The rest of the instructions won't talk about pyenv.

2.  Install uv in your user account, by following the instructions
    at `https://docs.astral.sh/uv/getting-started/installation/`.

3.  Then to install the base dependencies needed to run the server,
    navigate to the dir with the
    uv files (i.e., this subdir) and run

    ``` example
    uv sync
    ```

4. (Optional)
  There are also optional dependency groups that you can install for more
  functionality. These are utilized by plugins in the `natural4_exe/plugins`
  directory.
  To install all extra dependencies for maximum functionality, you can run

  ```example
  uv sync --all-extras
  ```
  
  - Alternatively, you can install them selectively to only enable those
    functionalities which you want.
    These dependency groups include:

    - The `docgen` group is used by the `plugins/docgen` plugin to turn
      markdown output to documents like `docx` and `pdf`.
      Note that for `pdf` output to work, you also need a `latex` engine
      installed.
      To install this dependency group, you can run

      ```example
      uv sync --extras docgen
      ```


You can run the scripts, with `uv run`.

# Optional: if you want to use `pre-commit`:

There is a `pre-commit` config with some basic checks and linters. If
you want to be able to run `pre-commit` locally:

First install `pre-commit` by following the instructions at
`https://pre-commit.com/#install` (if you are on a mac,
`brew install pre-commit`)

You then have a few options as to when to run it.

-   Get the `pre-commit` hooks to run automatically either on commit or
    on push. If you like making a lot of commits, you'd probably prefer
    to have the hooks run on push with `pre-commit install -t pre-push`
-   Run yourself at any time on your locally changed files:
    `pre-commit run`
-   Run yourself on all files in the repository:
    `pre-commit run --all-files`
-   Set up an editor hook to run on save

`pre-commit` can be useful even if you have a proper server-side CI,
because it's often more convenient to be able to uncover and debug or
fix the sorts of things that'd be checked by the linters locally, before
it gets to the CI runner.

# Running the web server
[Sanic](https://sanic.dev/en/) is both the web framework and the web server
that we use to deploy and run the app.
To run this, first `cd` into `gsheet/natural4-server/natural4_server`
and copy the `sanic.joe.py` file to say `sanic.user.py`.
Assuming that you have the gsheet repo in `/home/user`, you would run

```example
cd /home/user/gsheet/natural4-server/natural4_server

cp sanic.joe.py sanic.user.py
```

Be sure to adjust the variables there accordingly, in particular:
- the environment variables found in the `raw_env` string:
  - `V8K_WORKDIR`
  - `v8k_startport`
- the port number, ie the `port = ####` argument passed to `app.run`

The number of workers can be set by passing `fast = True` to `app.run` instead
of `workers = #`.
The `fast = True` option tells the Sanic server to automatically choose
the number of workers based on the number of cpu cores.
For instance, to run with 4 workers, you can set

```example
 app.run(
    host = '0.0.0.0', port = 8200,
    workers = 4,
    access_log = False,
    ssl = ssl
  )
```

With this, you can now run the app, powered by the Sanic server as a Python
script, ie

```example
uv run sanic.user.py
```

# DevMode

If you want to run a dev version of the Google Apps Script and pyrest
codebase, you can launch a new gunicorn instance on, say, port 8081.

If somewhere in the top ten lines of the spreadsheet you have something
like this, it will use that port instead

``` example
// live updates TRUE      devMode port 8081
```

If you're actively editing the spreadsheet and the redraws are slowing
you down, set live updates to FALSE.

# How Slots Work

Suppose you configure your `sanic.user.py` to run with

v8k_startport=8000

host='0.0.0.0'  
port='8888'

hello.py will call v8k, and v8k will launch `npm run serve` clones of
the `[[../vue-pure-pdpa/][vue-pure-pdpa]]` repo.

This will set up the following listening servers:

| port | listener                  | description                                                                                         |
|------|---------------------------|-----------------------------------------------------------------------------------------------------|
| 8888 | Sanic running hello.py | If your spreadsheet has devMode port, Code.gs will try to hit the pyrest API endpoint on this port. |
| 8000 | npm run serve             | managed by v8k                                                                                      |
| 8001 | npm run serve             | managed by v8k                                                                                      |
| 8002 | npm run serve             | managed by v8k                                                                                      |
| 8003 | npm run serve             | managed by v8k                                                                                      |
| 8004 | npm run serve             | managed by v8k                                                                                      |
| 8005 | npm run serve             | managed by v8k                                                                                      |
| 8006 | npm run serve             | managed by v8k                                                                                      |
| 8007 | npm run serve             | managed by v8k                                                                                      |
| 8008 | npm run serve             | managed by v8k                                                                                      |

If the spreadsheet does not have a `devMode port` the default is 8080.

The AWS instance is configured to open ports 8000 to 9000 so you can
pick your own combination of `bind` port and `startport`.

The convention is to have the `bind` port immediately below the
`startport`, i.e.

| port | listener                                     |
|------|----------------------------------------------|
| 8200 | gunicorn's bind port                         |
| 8201 | the startport configured in sanic.user.py    |

If there are multiple users on the server, you can each agree amongst
yourselves to each squat on a different set of 10 ports.

By default, the v8k poolsize is 9.
To change this, edit the `sanic.user.py` file and add a new environment
variable `V8K_SLOTS = #` to the `raw_env` string, eg:

```example

raw_env: str = '''
basedir=.
V8K_WORKDIR=/home/joe/v8k_workdir
v8k_startport=8201
v8k_path=/home/mengwong/src/smucclaw/vue-pure-pdpa/bin/v8k
V8K_SLOTS=20
'''

```

# SSL background

1.  did Let's Encrypt with CertBot \[2022-07-10 Sun\]
    <https://certbot.eff.org/instructions?ws=other&os=ubuntufocal>

2.  set up a cname from cclaw.legalese.com to the AWS instance

3.  run sanic with certfile and keyfile
    ie adjust the `ssl` variable in `sanic.user.py` accordingly:

    ```example
    ssl: dict[str, str] = {
      'cert': path_to_certfile,
      'key': path_to_private_key
    }
    ```

4.  now the SVG and PNG should work in the sidebar main.html

# The User Experience, Broken Down Step By Step

see architecture.dot for illustration

# Invoke from command-line

``` bash
curl localhost:8020/post -F uuid="23fcb41d-4438-45f4-976e-16174109df02" -F spreadsheetId="1GdDyNl6jWaeSwY_Ao2sA8yahQINPcnhRh9naGRIDGak" -F sheetId="1206725099" -F "csvString=<$filename.csv"
```
