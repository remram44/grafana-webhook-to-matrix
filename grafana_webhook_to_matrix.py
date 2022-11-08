import aiohttp
from aiohttp import web
from datetime import datetime
import os


homeserver = os.environ['MATRIX_HOMESERVER']
access_token = os.environ['MATRIX_ACCESS_TOKEN']
room = os.environ['MATRIX_ROOM']


_last_timestamp = 0
_counter = 0

def unique_number():
    global _last_timestamp
    global _counter
    timestamp = int(datetime.utcnow().timestamp())
    if timestamp == _last_timestamp:
        _counter += 1
    else:
        _counter = 0
    _last_timestamp = timestamp
    return timestamp * 100 + _counter


async def send_message(text):
    async with aiohttp.ClientSession() as http:
        txid = unique_number()
        res = await http.put(
            f'https://{homeserver}/_matrix/client/v3/rooms/{room}'
            + f'/send/m.room.message/{txid}',
            headers={'Authorization': f'Bearer {access_token}'},
            json={
                'msgtype': 'm.text',
                'body': text,
            },
        )
        res.raise_for_status()


async def handle_alert(request):
    body = await request.json()
    title = body['title']
    status = body['status']
    await send_message(f'[{status}] {title}')
    return web.Response(text='Ok')


app = web.Application()
app.add_routes([
    web.post('/alert', handle_alert)
])


if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=8003)
