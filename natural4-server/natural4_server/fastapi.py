import logging
import os
import sys
import anyio
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


basedir = anyio.Path(os.environ.get("basedir", "."))

template_dir: anyio.Path = basedir / "template"
temp_dir: anyio.Path = basedir / "temp"
static_dir: anyio.Path = basedir / "static"
natural4_dir: anyio.Path = anyio.Path(os.environ.get("NL4_WORKDIR", temp_dir / "workdir"))

logger = logging.getLogger("uvicorn.error")

app = FastAPI()

app.mount("/workdir", StaticFiles(directory=natural4_dir), name="static")


@app.get("/aasvg/{uuid}/{ssid}/{sid}/{image}")
async def show_aasvg_image(uuid: str, ssid: str, sid: str, image: str) -> FileResponse:
    print("show_aasvg_image: handling request for /aasvg/ url", file=sys.stderr)

    image_path = natural4_dir / uuid / ssid / sid / "aasvg" / "LATEST" / image
    print(f"show_aasvg_image: sending path {image_path}", file=sys.stderr)

    return FileResponse(image_path)
