try:
  from query_le import query_le
except ImportError as exc:
  def query_le(_le_prog: str, _scenario_name: str, _query_name: str) -> str:
    return f'Failed to load SWI-Prolog: {exc}'