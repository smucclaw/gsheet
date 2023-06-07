try:
  from .analyse_state_space import get_maude_tasks
except ImportError:
  get_maude_tasks = lambda _natural4_file, _maude_output_path: None