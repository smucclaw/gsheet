try:
  from .pandoc_md_to_word_and_pdf import pandoc_md_to_word_and_pdf
except ImportError:
  pandoc_md_to_word_and_pdf = lambda _uuid_ss_folder, _timestamp: None