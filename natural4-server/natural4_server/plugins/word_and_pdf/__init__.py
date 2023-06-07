try:
  from .pandoc_md_to_outputs import get_pandoc_tasks
except ImportError:
  get_pandoc_tasks = lambda _uuid_ss_folder, _timestamp: None