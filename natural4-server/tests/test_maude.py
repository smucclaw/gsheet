from pathlib import Path

from natural4_server.plugins.natural4_maude.analyse_state_space import get_maude_tasks


def test_get_maude_tasks():
    natural4_file = Path("natural4_maude") / "examples" / "loan-agreement.natural4"
    output_path = Path(".temp")
    get_maude_tasks(natural4_file, output_path)

