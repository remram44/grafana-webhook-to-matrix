import aiohttp
from aiohttp import web
import base64
from datetime import datetime
import os


secret = os.environ['SECRET_TOKEN']


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


async def send_message(homeserver, access_token, room, text):
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
    try:
        header = request.headers["authorization"]
    except KeyError:
        raise web.HTTPBadRequest()
    if header.startswith('Bearer '):
        header = header[7:]
    try:
        token, homeserver, access_token, room = header.split('-')
    except ValueError:
        raise web.HTTPBadRequest()
    token = base64.b64decode(token).decode('ascii')
    homeserver = base64.b64decode(homeserver).decode('ascii')
    access_token = base64.b64decode(access_token).decode('ascii')
    room = base64.b64decode(room).decode('ascii')
    if token != secret:
        raise web.HTTPForbidden()

    body = await request.json()
    await send_message(homeserver, access_token, room, body['message'])
    return web.Response(text='Ok')


app = web.Application()
app.add_routes([
    web.post('/alert', handle_alert)
])


if __name__ == '__main__':
    web.run_app(app, port=8003)
