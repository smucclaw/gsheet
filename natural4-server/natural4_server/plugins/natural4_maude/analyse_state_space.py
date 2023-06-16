import asyncio
from collections.abc import AsyncGenerator
import os
import pathlib

from cytoolz.functoolz import *
from cytoolz.curried import *

import anyio

import maude
from natural4_server.task import Task

from .visualise import (
  init_maude_n_load_main_file,
  config_to_html_file,
  natural4_rules_to_config,
  natural4_rules_to_race_cond_htmls
)

maude_main_file: pathlib.Path = pathlib.Path('plugins') / 'natural4_maude' / 'main.maude'
maude_main_mod = init_maude_n_load_main_file(maude_main_file)

@curry
def gen_state_space_and_find_race_cond(
  output_path: str | os.PathLike,
  config: maude.Term,
  natural4_rules: str
):
  '''
  Generate state space graph and generate race condition traces.
  Note that the former may take forever as it uses FailFreeGraph.expand, which
  does not terminate if the state space is infinite.
  '''

  config_to_html_file(
    maude_main_mod, config, 'all *',
    pathlib.Path(output_path) / 'LATEST_state_space.html'
  )

  natural4_rules_to_race_cond_htmls(
    maude_main_mod,
    pathlib.Path(output_path) / 'LATEST_race_cond.html',
    natural4_rules
  )

async def get_maude_tasks(
  natural4_file: str | os.PathLike,
  output_path: str | os.PathLike
) -> AsyncGenerator[Task, None]:
  '''
  Post process textual natural4 files by using Maude to generate a state space
  and find a race condition trace.
  '''

  # Read the textual natural4 file.
  # maude_path = Path(uuid_ss_folder) / 'maude'
  output_path = anyio.Path(output_path)
  await output_path.mkdir(parents=True, exist_ok=True)
  # natural4_file = maude_path / 'LATEST.natural4'
  async with await anyio.open_file(natural4_file) as f:
    natural4_rules: str = (await f.read()).strip()

  # We don't proceed with post processing if the natural4 file is empty or
  # contains only whitespaces.
  if natural4_rules:
    # Transform the set of rules into the initial configuration of the
    # transition system.
    config: maude.Term | None = await asyncio.to_thread(
      natural4_rules_to_config,
      maude_main_mod, natural4_rules
    )
    # Do we need to worry about this being None?
    if config:
      yield Task(
        func = gen_state_space_and_find_race_cond,
        args = (output_path, config, natural4_rules)
      )