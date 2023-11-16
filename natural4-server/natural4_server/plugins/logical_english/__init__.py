try:
  from .query_le import query_le
except ImportError as exc:
  async def query_le(query_params: dict[str, str]) -> str:
    return f'Failed to load SWI-Prolog: {exc}'