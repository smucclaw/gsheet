import asyncio
from collections.abc import Awaitable, Generator
import os
from pathlib import Path

from cytoolz.functoolz import *
from cytoolz.curried import *

import maude

from .visualise import (
  init_maude_n_load_main_file,
  config_to_html_file,
  natural4_rules_to_config,
  natural4_rules_to_race_cond_htmls
)

maude_main_file = Path('plugins') / 'natural4_maude' / 'main.maude'
maude_main_mod = init_maude_n_load_main_file(maude_main_file)

@curry
def gen_state_space(
  output_path: str | os.PathLike,
  config: maude.Term
) -> Awaitable[None]:
  '''
  Generate state space graph.
  graph.expand() in FailFreeGraph may take forever because the state
  space may be infinite.
  '''

  return asyncio.to_thread(
    config_to_html_file,
    maude_main_mod, config, 'all *',
    output_path / 'LATEST_state_space.html'
  )

@curry
def find_race_cond(
  output_path: str | os.PathLike,
  natural4_rules: str
) -> Awaitable[None]:
  '''
  Find a trace with race conditions and generate a graph.
  '''

  return asyncio.to_thread(
    natural4_rules_to_race_cond_htmls,
    maude_main_mod,
    output_path / 'LATEST_race_cond.html',
    natural4_rules
  )

@curry
def get_maude_tasks(
  natural4_file: str | os.PathLike,
  output_path: str | os.PathLike
) -> Generator[Awaitable[None], None, None]:
  '''
  Post process textual natural4 files by using Maude to generate a state space
  and find a race condition trace.
  '''

  # Read the textual natural4 file.
  # maude_path = Path(uuid_ss_folder) / 'maude'
  output_path = Path(output_path)
  output_path.mkdir(parents=True, exist_ok=True)
  # natural4_file = maude_path / 'LATEST.natural4'
  with open(natural4_file) as f:
    natural4_rules = f.read()

  # We don't proceed with post processing if the natural4 file is empty or
  # contains only whitespaces.
  if natural4_rules.strip():
    # Transform the set of rules into the initial configuration of the
    # transition system.
    config = natural4_rules_to_config(
      maude_main_mod, natural4_rules
    )
    # Do we need to worry about this being None?
    if config:
      yield find_race_cond(output_path, natural4_rules)
      yield gen_state_space(output_path, config)

      # try:
      #   async with (asyncio.timeout(15), asyncio.TaskGroup() as tasks):
      #     tasks.create_task(find_race_cond(output_path, natural4_rules))
      #     tasks.create_task(gen_state_space(output_path, config))
      # except TimeoutError:
      #   # Continue along the happy path even if we get a timeout
      #   print("Natural4 Maude timeout", file=sys.stderr)

# run_analyse_state_space = compose_left(
#   analyse_state_space, asyncio.run
# )