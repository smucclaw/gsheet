try:
  import janus_swi as janus

  janus.consult('le.qlf')

  def query_le(le_prog, scenario_name, query_name):

    swipl_query_str = 'le_answer:parse_and_query_and_explanation(\"test\", en(LE_prog), LE_query, with(LE_scenario), JustificationHtml)'
    swipl_query_params = {
      'LE_prog': le_prog,
      'LE_scenario': scenario_name,
      'LE_query': query_name
    }

    result = janus.query_once(swipl_query_str, swipl_query_params)

    return result['JustificationHtml']

except ImportError:
  def query_le(_le_prog, _scenario_name, _query_name):
    return ''