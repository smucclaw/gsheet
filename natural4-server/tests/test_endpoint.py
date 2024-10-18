from asyncio import sleep
import json
import os
import re
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

    await sleep(1)

    response_json = json.loads(response.body)
    v8k_url = response_json["v8k_url"]
    qq = re.compile(r"/webapp/809(\d)/")
    slot_str = qq.search(v8k_url).group(1)
    slot = int(slot_str)-1
    
    print(f"V8K_WORKDIR = {os.environ['V8K_WORKDIR']}/vue-{slot:02}")
    assert response.status == 200