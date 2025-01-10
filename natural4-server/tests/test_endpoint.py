from sanic import Sanic
from sanic_testing.reusable import ReusableClient
from time import sleep

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

            sleep(1)

            request, response_json = client.get(f'{workdir_url}/petri/LATEST.png')
            assert response_json.status == 200

            request, response_json = client.get(f'{workdir_url}/petri/LATEST.svg')
            assert response_json.status == 200

            request, response_json = client.get(f'{workdir_url}/petri/LATEST-small.png')
            assert response_json.status == 200