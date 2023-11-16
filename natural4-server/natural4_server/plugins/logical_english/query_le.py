import asyncio
import pathlib

import janus_swi as janus

_le_qlf_path: pathlib.Path = pathlib.Path('plugins') / 'logical_english' / 'le.qlf'

# TODO: Implement query_le_with_new_data
def _query_le(query_params: dict[str, str]) -> str:
  janus.attach_engine()
  janus.consult(f'{_le_qlf_path}')

  result = janus.apply_once(
    'le_answer', 'parse_en_and_query_and_explanation',
    query_params['le_prog'],
    query_params['query_name'],
    query_params.get('scenario_name', '')
  )

  janus.detach_engine()

  return result

  # while True:
  #   try:
  #     janus.detach_engine()
  #   except Exception:
  #     break

  # match result:
  #   case {'truth': True, 'JustificationHtml': justification_html}:
  #     return justification_html
  #   case _:
  #     return 'Logical English query failed!'

async def query_le(query_params: dict[str, str]) -> str:
  return await asyncio.to_thread(_query_le, query_params)