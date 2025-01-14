import asyncio
from collections.abc import AsyncGenerator, Collection, Sequence
import os
import sys

from cytoolz.functoolz import *
from cytoolz.itertoolz import *
from cytoolz.curried import *

import pyrsistent as pyrs

import anyio

import pypandoc

from natural4_server.task import Task


class PandocOutput(pyrs.PRecord):
    file_extension = pyrs.field(mandatory=True, type=str)
    extra_args = pyrs.field(Sequence, initial=())


pandoc_outputs: Collection[PandocOutput] = pyrs.s(
    PandocOutput(file_extension="docx", extra_args=("-f", "markdown+hard_line_breaks", "-s")),
    PandocOutput(
        file_extension="pdf",
        extra_args=(
            "--pdf-engine=xelatex",
            "-V",
            "CJKmainfont=Droid Sans Fallback",
            "-f",
            "markdown+hard_line_breaks",
            "-s",
        ),
    ),
)

pandoc_path = pypandoc.get_pandoc_path()


async def pandoc_md_to_output(
    uuid_ss_folder: str | os.PathLike,
    timestamp: str | os.PathLike,
    pandoc_output: PandocOutput,
) -> None:
    uuid_ss_folder_path = anyio.Path(uuid_ss_folder)
    md_file: anyio.Path = uuid_ss_folder_path / "md" / "LATEST.md"  # f'{timestamp}.md'

    if await md_file.exists():
        match pandoc_output:
            case {"file_extension": file_extension, "extra_args": extra_args}:
                outputpath: anyio.Path = uuid_ss_folder_path / file_extension
                await outputpath.mkdir(parents=True, exist_ok=True)

                timestamp_file: str = f"{timestamp}.{file_extension}"
                outputfile: anyio.Path = outputpath / timestamp_file

                pandoc_cmd = (
                    pandoc_path,
                    "-o",
                    f"{outputfile}",
                    *extra_args,
                    f"{md_file}",
                )
                print(f'Running {" ".join(pandoc_cmd)}', file=sys.stderr)

                try:
                    proc = await asyncio.subprocess.create_subprocess_exec(
                        *pandoc_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()

                    if stdout:
                        print(f"[pandoc out]\n{stdout.decode()}")

                    if stderr:
                        print(f"[pandoc err]\n{stderr.decode()}")
                except RuntimeError as exc:
                    print(
                        f"Error occured while outputting to {file_extension}: {exc}",
                        file=sys.stderr,
                    )

                latest_file: anyio.Path = outputpath / f"LATEST.{file_extension}"
                await latest_file.unlink(missing_ok=True)
                await latest_file.symlink_to(timestamp_file)
            case _:
                pass


async def get_pandoc_tasks(
    # markdown_coro: Awaitable[asyncio.subprocess.Process],
    uuid_ss_folder: str | os.PathLike,
    timestamp: str | os.PathLike,
) -> AsyncGenerator[Task, None]:
    # markdown_proc: asyncio.subprocess.Process = await markdown_coro
    # await markdown_proc.wait()

    print("Markdown output done.", file=sys.stderr)

    for output in pandoc_outputs:
        yield Task(func=pandoc_md_to_output, args=(uuid_ss_folder, timestamp, output))
