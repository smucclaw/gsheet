from collections.abc import Mapping
import pyrsistent as pyrs
import janus_swi as janus

janus.consult('le.qlf')

# TODO: Implement query_le_with_new_data
def query_le(le_prog: str, scenario_name: str, query_name: str) -> str | None:
  swipl_query_str: str = '''
    le_answer:parse_and_query_and_explanation(
      "test", en(LE_prog), LE_query, with(LE_scenario), JustificationHtml
    )
  '''

  swipl_query_params: Mapping[str, str] = pyrs.m(
    LE_prog = le_prog,
    LE_scenario = scenario_name,
    LE_query = query_name
  )

  result = janus.query_once(swipl_query_str, inputs=swipl_query_params)

  match result:
    case {'truth': True, 'JustificationHtml': justification_html}:
      return justification_html
    case _:
      return 'Logical English query failed!'