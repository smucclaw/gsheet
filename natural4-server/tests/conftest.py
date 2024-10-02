import pytest

from natural4_server.hello import app as application_instance


@pytest.fixture
def app():
    return application_instance

@pytest.fixture
def post_data():
    return {
        "uuid": "e909063f-f7a2-4e6a-945c-f1b21314227d",
        "spreadsheetId": "1GdDyNl6jWaeSwY_Ao2sA8yahQINPcnhRh9naGRIDGak",
        "sheetId":"1206725099"
    }