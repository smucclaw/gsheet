from sanic import Sanic
import pytest

@pytest.mark.asyncio
async def test_live(app: Sanic):
    request, response = await app.asgi_client.get("/health/liveness")

    assert response.status == 200

@pytest.mark.asyncio
async def test_aasvg(app: Sanic):
    request, response = await app.asgi_client.get("/aasvg/787aa580-7c24-4b3e-bcc6-3b1c627153f7/1GdDyNl6jWaeSwY_Ao2sA8yahQINPcnhRh9naGRIDGak/1206725099/CoveredIf-full.svg")

    assert response.status == 200