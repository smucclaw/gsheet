try:
  from .flowchart_dot_to_outputs import get_flowchart_tasks
except ImportError:
  get_flowchart_tasks = lambda _uuid_ss_folder, _timestamp: None