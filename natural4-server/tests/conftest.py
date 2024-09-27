import pytest

from natural4_server.hello import app as application_instance


@pytest.fixture
def app():
    return application_instance