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
    request, response = await app.asgi_client.post('/post', data=post_data)

    assert response.status == 200