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
import datetime
import os
import pathlib
import resource
import signal
import sys
import typing
from collections.abc import Sequence

import anyio
import cytoolz.curried as cyz
import orjson
from sanic import HTTPResponse, Request, Sanic, file, json

from natural4_server.plugins.docgen.pandoc_md_to_outputs import pandoc_docx, pandoc_md_to_output, pandoc_pdf
from natural4_server.plugins.flowchart import get_flowchart_tasks
from natural4_server.task import run_tasks


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


default_filenm_natL4exe_from_stack_install = "natural4-exe"
natural4_exe: str = os.environ.get("natural4_exe", default_filenm_natL4exe_from_stack_install)

try:
    nl4exe_time_limit: float = float(os.environ["NL4EXE_TIME_LIMIT"])
except (KeyError, ValueError):
    # Here we're catching:
    # KeyError that could arise in accessing NL4EXE_TIME_LIMIT from the env
    # ValueError that could occur when casting that to a float.
    nl4exe_time_limit: float = 20

# see gunicorn.conf.py for basedir, workdir, startport
natural4_dir: pathlib.Path = pathlib.Path(os.environ.get("NL4_WORKDIR", pathlib.Path(os.getcwd()) / "temp" / "workdir/"))

app = Sanic("Larangan", dumps=orjson.dumps, loads=orjson.loads)

app.config.CORS_ORIGINS = "http://localhost:8000,https://smucclaw.github.io"


# ################################################
#            SERVE (MOST) STATIC FILES
# ################################################
#  secondary handler serves .l4, .md, .hs, etc static files

app.static("/workdir/", pathlib.Path(natural4_dir), name="workdir")

# ################################################
#            SERVE SVG STATIC FILES
# ################################################
# this is handled a little differently because
# the directory structure for SVG output is a bit
# more complicated than for the other outputs.
# There is a LATEST directory instead of a LATEST file
# so the directory path is a little bit different.


@app.route("/aasvg/<uuid>/<ssid>/<sid>/<image>")
async def show_aasvg_image(request: Request, uuid: str, ssid: str, sid: str, image: str) -> HTTPResponse:
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
    time_now: str = start_time.strftime("%Y%m%dT%H%M%S.%fZ")

    print(
        "\n--------------------------------------------------------------------------\n",
        file=sys.stderr,
    )
    print("hello.py processCsv() starting at ", start_time, file=sys.stderr)

    uuid, spreadsheet_id, sheet_id = extract_fields(request.form)

    target_folder = natural4_dir / uuid / spreadsheet_id / sheet_id

    target_path = await save_csv(request, target_folder, time_now)

    # ---------------------------------------------
    # call natural4-exe, wait for it to complete.
    # ---------------------------------------------

    # one can leave out the markdown by adding the --tomd option
    # one can leave out the ASP by adding the --toasp option
    create_files: Sequence[str] = (
        natural4_exe,
        f"--workdir={natural4_dir}",
        f"--uuiddir={pathlib.Path(uuid) / spreadsheet_id / sheet_id}",
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
            return json({"nl4_err": f"natural4_exe timed out after {nl4exe_time_limit} seconds."})

    print(
        f"hello.py main: back from natural4-exe (took {datetime.datetime.now() - start_time})",
        file=sys.stderr,
    )

    nl4_out, nl4_err = await nl4exe.communicate()
    nl4_out, nl4_err = nl4_out.decode(), nl4_err.decode()

    print(f"hello.py main: natural4-exe stdout length = {len(nl4_out)}", file=sys.stderr)
    print(f"hello.py main: natural4-exe stderr length = {len(nl4_err)}", file=sys.stderr)

    short_err_maxlen, long_err_maxlen = 2_000, 20_000
    nl4_stdout, nl4_stderr = nl4_out[:long_err_maxlen], nl4_err[:long_err_maxlen]

    if len(nl4_err) < short_err_maxlen:
        print(nl4_err)

    # ---------------------------------------------
    # postprocessing: for petri nets: turn the DOT files into PNGs
    # we run this asynchronously and block at the end before returning.
    # ---------------------------------------------
    timestamp, flowchart_tasks = await petri_post_process(target_folder)

    # ---------------------------------------------
    # postprocessing:
    # Use pandoc to generate word and pdf docs from markdown.
    # ---------------------------------------------
    app.add_task(pandoc_md_to_output(target_folder, timestamp, pandoc_docx))
    app.add_task(pandoc_md_to_output(target_folder, timestamp, pandoc_pdf))
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
        await anyio.open_file(target_folder / "aasvg" / "LATEST" / "index.html", "r") as aasvg_file,
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


async def petri_post_process(target_folder):
    petri_folder = target_folder / "petri"
    dot_path = anyio.Path(petri_folder / "LATEST.dot")
    # dot_path resolves to something like 2025-01-06T03:00:52.dot
    # stem is respectively a timestamp 2025-01-06T03:00:52
    timestamp = (await dot_path.readlink()).stem

    flowchart_tasks: asyncio.Task[None] = cyz.pipe(
        get_flowchart_tasks(target_folder, timestamp), run_tasks)

    return timestamp, flowchart_tasks


async def save_csv(request, target_folder, time_now):
    target_path = target_folder / f"{time_now}.csv"

    await anyio.Path(target_folder).mkdir(parents=True, exist_ok=True)

    async with await anyio.open_file(target_path, "w") as fout:
        await fout.write(request.form["csvString"][0])
    return target_path


def extract_fields(data):
    uuid: str = data["uuid"][0]
    spreadsheet_id: str = data["spreadsheetId"][0]
    sheet_id: str = data["sheetId"][0]
    return uuid, spreadsheet_id, sheet_id

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
