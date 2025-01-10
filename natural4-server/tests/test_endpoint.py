from time import sleep
from sanic import Sanic
import pytest
from sanic_testing.reusable import ReusableClient

# @pytest.mark.asyncio
# async def test_live(app: Sanic):
#     request, response = await app.asgi_client.get("/health/liveness")

#     assert response.status == 200

def test_post(app: Sanic, post_data):
    with open('tests/data/rodents.csv') as f:
        input_data = f.read()
        with ReusableClient(app) as client:
            post_data['csvString'] = input_data
            request, response_post = client.post('/post', data=post_data)
            assert response_post.status == 200

            workdir_url = f'/workdir/{post_data['uuid']}/{post_data['spreadsheetId']}/{post_data['sheetId']}'

            request, response_json = client.get(f'{workdir_url}/aajson/LATEST.json')
            assert response_json.status == 200

            sleep(10)
            request, response_pdf = client.get(f'{workdir_url}/pdf/LATEST.pdf')
            assert response_pdf.status == 200
