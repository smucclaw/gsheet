try:
  from .analyse_state_space import analyse_state_space
except ImportError:
  analyse_state_space = lambda _natural4_file, _maude_output_path: None