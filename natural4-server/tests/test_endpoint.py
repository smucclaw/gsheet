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

    assert response.status == 200
    await sleep(1)

    response_json = json.loads(response.body)
    v8k_url = response_json["v8k_url"]
    qq = re.compile(r"/webapp/809(\d)/")
    slot_str = qq.search(v8k_url).group(1)
    slot = int(slot_str)-1
    
    vue_dir = f"{os.environ['V8K_WORKDIR']}/vue-{slot:02}"

    interview_purs_stats = os.stat(vue_dir + "/anyall-purs/src/RuleLib/Interview.purs")

    interview_aajson_stats = os.stat(vue_dir + "/src/assets/Interview.json")

    assert interview_purs_stats.st_size == 10769
    assert interview_aajson_stats.st_size == 33577