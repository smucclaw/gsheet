try:
  from .flowchart_dot_to_outputs import flowchart_dot_to_outputs as run_flowchart_dot_to_outputs
except ImportError:
  run_flowchart_dot_to_outputs = lambda _uuid_ss_folder, _timestamp: None