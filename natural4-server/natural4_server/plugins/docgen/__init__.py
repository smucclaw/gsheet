from collections.abc import Awaitable, Generator
import os

from cytoolz.functoolz import curry

try:
  from .pandoc_md_to_outputs import get_pandoc_tasks
except ImportError:
  @curry
  def get_pandoc_tasks(
    natural4_exe: str,
    natural4_dir: str | os.PathLike,
    uuiddir: str | os.PathLike,
    target_path: str | os.PathLike,
    uuid_ss_folder: str | os.PathLike,
    timestamp: str
  ) -> Generator[Awaitable[None], None, None]:
    return