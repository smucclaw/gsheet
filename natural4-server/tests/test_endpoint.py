from time import sleep

from sanic import Sanic
from sanic.application.constants import ServerStage
from sanic_testing.reusable import ReusableClient
from tenacity import retry, retry_if_result, stop_after_delay, wait_fixed


def is_not_200(value):
    """Return True if value is None"""
    return value != 200

@retry(retry=(retry_if_result(is_not_200)), wait=wait_fixed(5), stop=stop_after_delay(30))
def poll_url(client, url):
    print(f"Waiting for {url}...")
    request, response = client.get(url)
    return response.status


def test_post(app: Sanic, post_data):
    with open("tests/data/rodents.csv") as f:
        input_data = f.read()
        with ReusableClient(app) as client:
            for info in app.state.server_info:
                info.stage = ServerStage.SERVING

            post_data["csvString"] = input_data
            request, response_post = client.post("/post", data=post_data)
            assert response_post.status == 200

            workdir_url = f'/workdir/{post_data['uuid']}/{post_data['spreadsheetId']}/{post_data['sheetId']}'

            request, response_json = client.get(f"{workdir_url}/aajson/LATEST.json")
            assert response_json.status == 200

            sleep(1)

            request, response_json = client.get(f"{workdir_url}/petri/LATEST.png")
            assert response_json.status == 200

            request, response_json = client.get(f"{workdir_url}/petri/LATEST.svg")
            assert response_json.status == 200

            request, response_json = client.get(f"{workdir_url}/petri/LATEST-small.png")
            assert response_json.status == 200

            response_docx = poll_url(client, f"{workdir_url}/docx/LATEST.docx")
            assert response_docx == 200

            response_pdf = poll_url(client, f"{workdir_url}/pdf/LATEST.pdf")

            assert response_pdf == 200
