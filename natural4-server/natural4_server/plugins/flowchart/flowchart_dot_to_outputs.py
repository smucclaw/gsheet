import asyncio
import os
import sys
from collections.abc import Collection, Sequence

import anyio
import pyrsistent as pyrs
import pyrsistent_extras as pyrse

class FlowchartOutput(pyrs.PRecord):
    suffix = pyrs.field(type=str, initial="")
    file_extension = pyrs.field(mandatory=True, type=str)

    args = pyrs.field(type=Sequence, initial=pyrse.sq())


flowchart_outputs: Collection[FlowchartOutput] = pyrs.s(
    FlowchartOutput(file_extension="png", args=pyrse.sq("-Gdpi=150")),
    FlowchartOutput(suffix="-small", file_extension="png", args=pyrse.sq("-Gdpi=72")),
    FlowchartOutput(file_extension="svg"),
)

async def _dot_file_to_output(
    dot_file: str | os.PathLike[str],
    output_file: str | os.PathLike[str],
    args: Sequence[str],
) -> None:
    output_file = anyio.Path(output_file)

    graphviz_cmd: Sequence[str] = (
        pyrse.sq("dot", f"-T{output_file.suffix[1:]}", f"{dot_file}") + pyrse.psequence(args) + pyrse.sq("-o", f"{output_file}")
    )  # type: ignore

    print(f'Calling graphviz with: {" ".join(graphviz_cmd)}', file=sys.stderr)

    await asyncio.subprocess.create_subprocess_exec(*graphviz_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)


async def flowchart_dot_to_output(
    uuid_ss_folder: str | os.PathLike,
    timestamp: str | os.PathLike,
    flowchart_output: FlowchartOutput,
) -> None:
    uuid_ss_folder_path = anyio.Path(uuid_ss_folder)
    output_path: anyio.Path = uuid_ss_folder_path / "petri"
    await output_path.mkdir(parents=True, exist_ok=True)
    dot_file: anyio.Path = output_path / "LATEST.dot"

    if await dot_file.exists():
        match flowchart_output:
            case {"suffix": suffix, "file_extension": file_extension, "args": args}:
                timestamp_file: str = f"{timestamp}{suffix}.{file_extension}"
                output_file: str = f"{output_path / timestamp_file}"

                print(f"Drawing {file_extension} from dot file", file=sys.stderr)
                print(f"Output file: {output_file}", file=sys.stderr)
                await _dot_file_to_output(dot_file, output_file, args)

                latest_file: anyio.Path = output_path / f"LATEST{suffix}.{file_extension}"
                try:
                    await latest_file.unlink(missing_ok=True)
                    await latest_file.symlink_to(timestamp_file)
                    # os.symlink(timestamp_file, latest_file)
                except Exception as exc:
                    print(
                        "hello.py main: got some kind of OS error to do with the unlinking and the symlinking",
                        file=sys.stderr,
                    )
                    print(f"hello.py main: {exc}", file=sys.stderr)
