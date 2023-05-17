import asyncio
from pathlib import Path

from cytoolz.functoolz import *
from cytoolz.curried import *

import natural4_maude.visualise as vis

maude_main_file = Path('natural4_maude') / 'main.maude'
maude_main_mod = vis.init_maude_n_load_main_file(maude_main_file)

def gen_state_space(output_path, config):
  '''
  Generate state space graph.
  graph.expand() in FailFreeGraph may take forever because the state
  space may be infinite.
  '''

  return asyncio.to_thread(
    vis.config_to_html_file,
    maude_main_mod, config, 'all *',
    output_path / 'LATEST_state_space.html'
  )

def find_race_cond(maude_path, natural4_rules):
  '''
  Find a trace with race conditions and generate a graph.
  '''

  return asyncio.to_thread(
    vis.natural4_rules_to_race_cond_htmls,
    maude_main_mod,
    maude_path / 'LATEST_race_cond.html',
    natural4_rules
  )

async def analyse_state_space(natural4_file, output_path):
  '''
  Post process textual natural4 files by using Maude to generate a state space
  and find a race condition trace.
  '''

  # Read the textual natural4 file.
  # maude_path = Path(uuid_ss_folder) / 'maude'
  output_path.mkdir(parents=True, exist_ok=True)
  # natural4_file = maude_path / 'LATEST.natural4'
  with open(natural4_file) as f:
    natural4_rules = f.read()

  # We don't proceed with post processing if the natural4 file is empty or
  # contains only whitespaces.
  if natural4_rules.strip():
    # Transform the set of rules into the initial configuration of the
    # transition system.
    config = vis.natural4_rules_to_config(
      maude_main_mod, natural4_rules
    )
    # Do we need to worry about this being None?
    if config:
      # PARTY natural4-server MAY WITHIN 10 seconds DO tasks
      # tasks IS A AsyncM ()
      # MEANS generate state space AND find race condition
      try:
        async with (asyncio.timeout(10), asyncio.TaskGroup() as tasks):
          tasks.create_task(gen_state_space(output_path, config))
          tasks.create_task(find_race_cond(output_path, natural4_rules))
      except asyncio.TimeoutError:
        # Continue along the happy path even if we get a timeout
        print("Natural4 Maude timeout")
        pass

run_analyse_state_space = compose_left(
  analyse_state_space, asyncio.run
)