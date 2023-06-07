try:
  from .pandoc_md_to_outputs import pandoc_md_to_outputs as run_pandoc_md_to_outputs
except ImportError:
  run_pandoc_md_to_outputs = lambda _uuid_ss_folder, _timestamp: None