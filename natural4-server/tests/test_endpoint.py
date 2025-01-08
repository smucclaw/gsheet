from time import sleep
from sanic import Sanic
import pytest

@pytest.mark.asyncio
async def test_live(app: Sanic):
    request, response = await app.asgi_client.get("/health/liveness")

    assert response.status == 200

@pytest.mark.asyncio
async def test_post(app: Sanic, post_data):
    with open('tests/data/rodents.csv') as f:  
        input_data = f.read()

    post_data['csvString'] = input_data
    request, response_post = await app.asgi_client.post('/post', data=post_data)
    assert response_post.status == 200

    workdir_url = f'/workdir/{post_data['uuid']}/{post_data['spreadsheetId']}/{post_data['sheetId']}'

    print(f'/{workdir_url}/aajson/LATEST.json')
    request, response_json = await app.asgi_client.get(f'{workdir_url}/aajson/LATEST.json')
    assert response_json.status == 200

    sleep(5)
    request, response_pdf = await app.asgi_client.get(f'{workdir_url}/pdf/LATEST.pdf')
    assert response_pdf.status == 200
