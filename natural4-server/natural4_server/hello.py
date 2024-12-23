# ################################################
#               ONLINE DOCUMENTATION
# ################################################
# please see https://docs.google.com/document/d/1EvyiQhSgapumBRt9UloRpwiRcgVhF-m65FVdAz3chfs/edit#
# software version: 1.1.3

# ################################################
#          INVOCATION AND CONFIGURATION
# ################################################
# There is no #! line because we are run out of gunicorn.

import asyncio
from collections.abc import AsyncGenerator, Sequence
import datetime
import os
import pathlib
import sys
import typing

import anyio
import aiostream
import orjson

from sanic import HTTPResponse, Request, Sanic, file, json

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

from natural4_server.task import Task, run_tasks
from natural4_server.plugins.docgen import get_pandoc_tasks
from natural4_server.plugins.flowchart import get_flowchart_tasks

##########################################################
# SETRLIMIT to kill gunicorn runaway workers after a certain number of cpu seconds
# cargo-culted from https://www.geeksforgeeks.org/python-how-to-put-limits-on-memory-and-cpu-usage/
##########################################################

import signal
import resource


# checking time limit exceed
def time_exceeded(signo, frame) -> typing.NoReturn:
    print("hello.py: setrlimit time exceeded, exiting")
    raise SystemExit(1)


def set_max_runtime(seconds) -> None:
    # setting up the resource limit
    soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, hard))
    signal.signal(signal.SIGXCPU, time_exceeded)


# max run time
set_max_runtime(10000)

########################################################## end of setrlimit

basedir = anyio.Path(os.environ.get("basedir", "."))

default_filenm_natL4exe_from_stack_install = "natural4-exe"
natural4_exe: str = os.environ.get(
    "natural4_exe", default_filenm_natL4exe_from_stack_install
)

try:
    nl4exe_time_limit: float = float(os.environ["NL4EXE_TIME_LIMIT"])
except (KeyError, ValueError):
    # Here we're catching:
    # KeyError that could arise in accessing NL4EXE_TIME_LIMIT from the env
    # ValueError that could occur when casting that to a float.
    nl4exe_time_limit: float = 20

# sometimes it is desirable to override the default name
# that `stack install` uses with a particular binary from a particular commit
# in which case you would set up gunicorn.conf.py with a natural4_exe = natural4-noqns or something like that

# see gunicorn.conf.py for basedir, workdir, startport
template_dir: anyio.Path = basedir / "template"
temp_dir: anyio.Path = basedir / "temp"
static_dir: anyio.Path = basedir / "static"
natural4_dir: anyio.Path = anyio.Path(
    os.environ.get("NL4_WORKDIR", temp_dir / "workdir")
)

app = Sanic("Larangan", dumps=orjson.dumps, loads=orjson.loads)

app.static("/static", pathlib.Path(static_dir))
app.config.CORS_ORIGINS = "http://localhost:8000,https://smucclaw.github.io"
app.config.TEMPLATING_PATH_TO_TEMPLATES = pathlib.Path(template_dir)


# ################################################
#            SERVE (MOST) STATIC FILES
# ################################################
#  secondary handler serves .l4, .md, .hs, etc static files


@app.route("/workdir/<uuid>/<ssid>/<sid>/<channel>/<filename>")
async def get_workdir_file(
    request: Request, uuid: str, ssid: str, sid: str, channel: str, filename: str
) -> HTTPResponse:
    print(
        f"get_workdir_file: handling request for {uuid}/{ssid}/{sid}/{channel}/{filename}",
        file=sys.stderr,
    )

    workdir_folder: anyio.Path = natural4_dir / uuid / ssid / sid / channel
    workdir_folder_filename: anyio.Path = workdir_folder / filename

    response = HTTPResponse(status=204)

    if not await workdir_folder.exists():
        msg = f"get_workdir_file: unable to find workdir_folder {workdir_folder}"
    elif not await workdir_folder_filename.is_file():
        msg = f"get_workdir_file: unable to find file {workdir_folder_filename}"
    else:
        exts = {
            ".l4",
            ".epilog",
            ".purs",
            ".org",
            ".hs",
            ".ts",
            ".natural4",
            ".le",
            ".json",
        }
        if anyio.Path(filename).suffix in exts:
            mime_type, mime_type_str = ("text/plain",) * 2
        else:
            mime_type, mime_type_str = None, ""

        msg = f"get_workdir_file: returning {mime_type_str} {workdir_folder_filename}"

        response = await file(
            pathlib.Path(workdir_folder_filename), mime_type=mime_type
        )

    print(msg, file=sys.stderr)

    return response


# ################################################
#            SERVE SVG STATIC FILES
# ################################################
# this is handled a little differently because
# the directory structure for SVG output is a bit
# more complicated than for the other outputs.
# There is a LATEST directory instead of a LATEST file
# so the directory path is a little bit different.


@app.route("/aasvg/<uuid>/<ssid>/<sid>/<image>")
async def show_aasvg_image(
    request: Request, uuid: str, ssid: str, sid: str, image: str
) -> HTTPResponse:
    print("show_aasvg_image: handling request for /aasvg/ url", file=sys.stderr)

    image_path = natural4_dir / uuid / ssid / sid / "aasvg" / "LATEST" / image
    print(f"show_aasvg_image: sending path {image_path}", file=sys.stderr)

    return await file(pathlib.Path(image_path))


@app.route("/health/liveness")
async def liveness_probe(request: Request) -> HTTPResponse:
    return json({"status": "ok"})


# ################################################
#                      main
#      HANDLE POSTED CSV, RUN NATURAL4 & ETC
# This is the function that does all the heavy lifting.


@app.route("/post", methods=["GET", "POST"])
async def process_csv(request: Request) -> HTTPResponse:
    start_time: datetime.datetime = datetime.datetime.now()
    print(
        "\n--------------------------------------------------------------------------\n",
        file=sys.stderr,
    )
    print("hello.py processCsv() starting at ", start_time, file=sys.stderr)

    data = request.form

    uuid: str = data["uuid"][0]
    spreadsheet_id: str = data["spreadsheetId"][0]
    sheet_id: str = data["sheetId"][0]
    target_folder = anyio.Path(natural4_dir) / uuid / spreadsheet_id / sheet_id
    print(target_folder)
    time_now: str = datetime.datetime.now().strftime("%Y%m%dT%H%M%S.%fZ")
    target_file = anyio.Path(f"{time_now}.csv")
    # target_path is for CSV data
    target_path: anyio.Path = target_folder / target_file

    await target_folder.mkdir(parents=True, exist_ok=True)

    async with await anyio.open_file(target_path, "w") as fout:
        await fout.write(data["csvString"][0])

    # Generate markdown files asynchronously in the background.
    # uuiddir: anyio.Path = anyio.Path(uuid) / spreadsheet_id / sheet_id

    # markdown_cmd: Sequence[str] = (
    #   natural4_exe,
    #   '--only', 'tomd', f'--workdir={natural4_dir}',
    #   f'--uuiddir={uuiddir}',
    #   f'{target_path}'
    # )

    # print(f'hello.py child: calling natural4-exe {natural4_exe} (slowly) for tomd', file=sys.stderr)
    # print(f'hello.py child: {markdown_cmd}', file=sys.stderr)

    # Coroutine which is awaited before pandoc is called to generate documents
    # (ie word and pdf) from the markdown file.
    # markdown_coro: Awaitable[asyncio.subprocess.Process] = (
    #   asyncio.subprocess.create_subprocess_exec(
    #     *markdown_cmd,
    #     stdout = asyncio.subprocess.PIPE,
    #     stderr = asyncio.subprocess.PIPE
    #   )
    # )

    # ---------------------------------------------
    # call natural4-exe, wait for it to complete.
    # ---------------------------------------------

    # one can leave out the markdown by adding the --tomd option
    # one can leave out the ASP by adding the --toasp option
    create_files: Sequence[str] = (
        natural4_exe,
        # '--toasp', '--toepilog',
        f"--workdir={natural4_dir}",
        f"--uuiddir={anyio.Path(uuid) / spreadsheet_id / sheet_id}",
        f"{target_path}",
    )

    print(f"hello.py main: calling natural4-exe {natural4_exe}", file=sys.stderr)
    print(f'hello.py main: {" ".join(create_files)}', file=sys.stderr)

    nl4exe = asyncio.subprocess.create_subprocess_exec(
        *create_files, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        nl4exe = await asyncio.wait_for(nl4exe, timeout=nl4exe_time_limit)
    except TimeoutError:
        try:
            (await nl4exe).terminate()
        finally:
            return json(
                {
                    "nl4_err": f"natural4_exe timed out after {nl4exe_time_limit} seconds."
                }
            )

    print(
        f"hello.py main: back from natural4-exe (took {datetime.datetime.now() - start_time})",
        file=sys.stderr,
    )

    nl4_out, nl4_err = await nl4exe.communicate()
    nl4_out, nl4_err = nl4_out.decode(), nl4_err.decode()

    print(
        f"hello.py main: natural4-exe stdout length = {len(nl4_out)}", file=sys.stderr
    )
    print(
        f"hello.py main: natural4-exe stderr length = {len(nl4_err)}", file=sys.stderr
    )

    short_err_maxlen, long_err_maxlen = 2_000, 20_000
    nl4_stdout, nl4_stderr = nl4_out[:long_err_maxlen], nl4_err[:long_err_maxlen]

    if len(nl4_err) < short_err_maxlen:
        print(nl4_err)

    # ---------------------------------------------
    # postprocessing: for petri nets: turn the DOT files into PNGs
    # we run this asynchronously and block at the end before returning.
    # ---------------------------------------------
    uuid_ss_folder: anyio.Path = natural4_dir / uuid / spreadsheet_id / sheet_id
    petri_folder: anyio.Path = uuid_ss_folder / "petri"
    dot_path: anyio.Path = petri_folder / "LATEST.dot"
    timestamp: anyio.Path = anyio.Path((await dot_path.readlink()).stem)

    flowchart_tasks: asyncio.Task[None] = pipe(
        get_flowchart_tasks(uuid_ss_folder, timestamp), run_tasks, app.add_task
    )

    # Slow tasks below.
    # These are run in the background using app.add_background_task, which
    # adds them to Sanic's event loop.

    # ---------------------------------------------
    # postprocessing:
    # Use pandoc to generate word and pdf docs from markdown.
    # ---------------------------------------------
    pandoc_tasks: AsyncGenerator[Task | None, None] = get_pandoc_tasks(
        uuid_ss_folder, timestamp
    )

    # Concurrently peform the following:
    # - Write natural4-exe's stdout to a file.
    # - Write natural4-exe's stderr to a file.

    async with (
        await anyio.open_file(target_folder / f"{time_now}.out", "w") as out_file,
        await anyio.open_file(target_folder / f"{time_now}.err", "w") as err_file,
        asyncio.TaskGroup() as taskgroup,
    ):
        taskgroup.create_task(out_file.write(nl4_out))
        taskgroup.create_task(err_file.write(nl4_err))

    # Once v8k up returns with the vue purs post processing task, we create a
    # new process and get it to run the slow tasks concurrently.
    # These include:
    # - Pandoc tasks
    # - vue purs task
    slow_tasks = aiostream.stream.chain(pandoc_tasks)

    # Schedule all the slow tasks to run in the background.
    app.add_task(run_tasks(slow_tasks))

    # ---------------------------------------------
    # construct other response elements and log run-timings.
    # ---------------------------------------------

    end_time: datetime.datetime = datetime.datetime.now()
    elapsed_time: datetime.timedelta = end_time - start_time

    print(
        f"hello.py process_csv ready to return at {end_time} (total {elapsed_time})",
        file=sys.stderr,
    )

    # Concurrently:
    # - Wait for the flowcharts to be generated before returning to the sidebar.
    # - Read in the aasvg html file to return to the sidebar.
    async with (
        await anyio.open_file(
            uuid_ss_folder / "aasvg" / "LATEST" / "index.html", "r"
        ) as aasvg_file,
        asyncio.TaskGroup() as taskgroup,
    ):
        aasvg_index_task: asyncio.Task[str] = taskgroup.create_task(aasvg_file.read())
        await flowchart_tasks

    return json(
        {
            "nl4_stdout": nl4_stdout,
            "nl4_err": nl4_stderr,
            "v8k_url": "",
            "aasvg_index": aasvg_index_task.result(),
            "timestamp": f"{timestamp}",
        }
    )

    # ---------------------------------------------
    # return to sidebar caller
    # ---------------------------------------------


# ################################################
# run when not launched via gunicorn
# ################################################

# This should only be ran while in debugging, and not in production
# The debugging werkzeug server cannot have be both a multi-threaded
# and multi-process at the same time.
# For local development purposes this running it as a
# multi-process server is fine, change if needed
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
