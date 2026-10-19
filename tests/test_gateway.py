import asyncio
import base64
import json
from pathlib import Path
from urllib.parse import urlsplit

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from moss_runtime.gateway import (create_app, authorized, normalize_origin,
                                 public_origin_from_environment, origin_allowed)

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = 'test-password-for-gateway'
AUTH = {'Authorization': 'Basic ' + base64.b64encode(('moss:' + PASSWORD).encode()).decode()}
POD_ID = 'releasepod1234'
POD_ORIGIN = 'https://' + POD_ID + '-8188.proxy.runpod.net'


def test_origin_normalization_and_invalid_values():
    assert normalize_origin('HTTPS://EXAMPLE.COM:443') == ('https', 'example.com', 443)
    assert normalize_origin('http://localhost:80') == ('http', 'localhost', 80)
    assert normalize_origin('http://[::1]:8188') == ('http', '::1', 8188)
    assert normalize_origin('http://[0:0:0:0:0:0:0:1]:8188') == ('http', '::1', 8188)
    assert normalize_origin('https://bücher.example') == ('https', 'xn--bcher-kva.example', 443)
    assert origin_allowed('https://example.com', 'EXAMPLE.COM:443', None)
    for invalid in ('null', '', 'https://user:secret@example.com', 'https://example.com/',
                    'https://example.com/path', 'https://example.com?x=1',
                    'https://example.com#fragment', 'https://example.com?',
                    'https://example.com#', ' https://example.com',
                    'https://example.com\n', 'https://one.example https://two.example',
                    'https://example.com:0', 'https://example.com:65536',
                    'https://example.com:', 'https://example.com\\evil', 'file://example.com',
                    'https://[broken', 'https://example.com,evil.example'):
        assert normalize_origin(invalid) is None, invalid
        assert not origin_allowed(invalid, 'example.com', None)


def test_public_origin_configuration_is_explicit_and_validated(monkeypatch):
    monkeypatch.delenv('MOSS_PUBLIC_ORIGIN', raising=False)
    monkeypatch.setenv('RUNPOD_POD_ID', POD_ID)
    expected = ('https', 'releasepod1234-8188.proxy.runpod.net', 443)
    assert public_origin_from_environment() == expected
    assert origin_allowed(POD_ORIGIN + ':443', '10.2.3.4:8188', expected)
    assert not origin_allowed(POD_ORIGIN.replace('https:', 'http:'), '10.2.3.4:8188', expected)
    assert not origin_allowed('http://10.2.3.4:8188', '10.2.3.4:8188', expected)
    monkeypatch.setenv('MOSS_PUBLIC_ORIGIN', 'https://studio.example:8443')
    assert public_origin_from_environment() == ('https', 'studio.example', 8443)
    monkeypatch.setenv('MOSS_PUBLIC_ORIGIN', 'https://studio.example/unexpected-path')
    with pytest.raises(ValueError, match='MOSS_PUBLIC_ORIGIN'):
        create_app({'ready': True}, ROOT, PASSWORD)
    monkeypatch.delenv('MOSS_PUBLIC_ORIGIN')
    monkeypatch.setenv('RUNPOD_POD_ID', 'bad/id')
    with pytest.raises(ValueError, match='RUNPOD_POD_ID'):
        create_app({'ready': True}, ROOT, PASSWORD)
    monkeypatch.setenv('RUNPOD_POD_ID', 'a' * 59)
    with pytest.raises(ValueError, match='RUNPOD_POD_ID'):
        create_app({'ready': True}, ROOT, PASSWORD)


def test_runpod_rewritten_host_allows_own_browser_post_and_websocket(monkeypatch):
    monkeypatch.delenv('MOSS_PUBLIC_ORIGIN', raising=False)
    monkeypatch.setenv('RUNPOD_POD_ID', POD_ID)

    async def run():
        seen = []
        async def endpoint(request):
            seen.append(dict(request.headers))
            if request.path == '/ws':
                ws = web.WebSocketResponse()
                await ws.prepare(request)
                async for message in ws:
                    await ws.send_str(message.data)
                return ws
            return web.json_response({'accepted': await request.json()})
        upstream = web.Application()
        upstream.router.add_route('*', '/{path:.*}', endpoint)
        async with TestServer(upstream) as server:
            app = create_app({'ready': True}, ROOT, PASSWORD, upstream=str(server.make_url('')).rstrip('/'))
            async with TestClient(TestServer(app)) as client:
                headers = {**AUTH, 'Host': '10.2.3.4:8188',
                           'Origin': POD_ORIGIN}
                response = await client.post('/prompt', headers=headers, json={'owned_test': True})
                assert response.status == 200
                assert (await response.json())['accepted'] == {'owned_test': True}
                async with client.ws_connect('/ws?clientId=owned-test', headers=headers) as ws:
                    await ws.send_str('owned event')
                    assert (await asyncio.wait_for(ws.receive(), 2)).data == 'owned event'
                for origin in ('https://attacker.example', 'http://10.2.3.4:8188', 'null'):
                    spoofed = {**headers, 'Origin': origin, 'X-Forwarded-Host': 'attacker.example',
                               'Forwarded': 'proto=https;host=attacker.example'}
                    assert (await client.post('/prompt', headers=spoofed, json={})).status == 403
                    with pytest.raises(aiohttp.WSServerHandshakeError) as error:
                        await client.ws_connect('/ws?clientId=blocked-test', headers=spoofed)
                    assert error.value.status == 403
        assert len(seen) == 2
        assert all('Authorization' not in headers and 'Origin' not in headers for headers in seen)
    asyncio.run(run())


def test_unicode_password_and_invalid_login():
    secret = 'valid-unicode-password-🔐'
    header = 'Basic ' + base64.b64encode(('moss:' + secret).encode()).decode()
    assert authorized(header, secret)
    assert not authorized(header, PASSWORD)
    bad_user = 'Basic ' + base64.b64encode('móss:incorrect'.encode()).decode()
    assert not authorized(bad_user, secret)


def test_preparation_auth_and_serverless_isolation():
    async def run():
        state = {'ready': False, 'phase': 'downloading', 'detail': 'Preparing models'}
        async with TestClient(TestServer(create_app(state, ROOT, PASSWORD))) as client:
            assert (await client.get('/healthz')).status == 200
            assert (await client.get('/readyz')).status == 503
            assert (await client.get('/ping')).status == 204
            for path in ('/', '/moss/status', '/object_info', '/ws', '/view?filename=private.png'):
                assert (await client.get(path)).status == 401
            assert (await client.get('/', headers={'Authorization': 'Basic !!bad'})).status == 401
            response = await client.get('/', headers=AUTH)
            assert 'Preparing models' in await response.text()
            assert (await client.post('/prompt', headers=AUTH, json={})).status == 503
            state.update(ready=True, phase='ready')
            assert (await client.get('/readyz')).status == 200
            html = await (await client.get('/', headers=AUTH)).text()
            assert '?template=photography-bf16&amp;source=moss' in html
            assert html.count('Open workflow') == 4
            assert 'http-equiv="refresh"' not in html
            assert (await client.get('/', headers={**AUTH, 'Origin': 'https://unrelated.example'})).status == 403
        async with TestClient(TestServer(create_app(state, ROOT, '', mode='serverless'))) as client:
            assert (await client.get('/readyz')).status == 200
            assert (await client.get('/', headers=AUTH)).status == 404
            assert (await client.get('/object_info', headers=AUTH)).status == 404
    asyncio.run(run())


def test_proxy_http_websocket_and_credentials_stay_at_gateway():
    async def run():
        # Reproduce the relevant pinned ComfyUI origin middleware behavior:
        # browser Origin must match a loopback Host, including explicit ports.
        @web.middleware
        async def comfy_origin_guard(request, handler):
            if request.headers.get('Sec-Fetch-Site') == 'cross-site':
                return web.Response(status=403)
            if 'Host' in request.headers and 'Origin' in request.headers:
                host = urlsplit('//' + request.headers['Host'].lower())
                origin = urlsplit(request.headers['Origin'].lower())
                host_domain = host.netloc if origin.port is not None else host.hostname
                origin_domain = origin.netloc if host.port is not None else origin.hostname
                if host.hostname in ('127.0.0.1', 'localhost', '::1') and host_domain != origin_domain:
                    return web.Response(status=403)
            return await handler(request)

        upstream = web.Application(middlewares=[comfy_origin_guard])
        seen = []
        async def endpoint(request):
            seen.append(dict(request.headers))
            if request.path == '/ws':
                ws = web.WebSocketResponse()
                await ws.prepare(request)
                async for message in ws:
                    if message.type == aiohttp.WSMsgType.TEXT:
                        await ws.send_str(message.data)
                    elif message.type == aiohttp.WSMsgType.BINARY:
                        await ws.send_bytes(message.data)
                return ws
            return web.json_response({'path': str(request.rel_url), 'body': await request.text()})
        upstream.router.add_route('*', '/{path:.*}', endpoint)
        async with TestServer(upstream) as server:
            app = create_app({'ready': True}, ROOT, PASSWORD, upstream=str(server.make_url('')).rstrip('/'))
            async with TestClient(TestServer(app)) as client:
                browser_headers = {**AUTH, 'Host': 'example-8188.proxy.runpod.net',
                                   'Origin': 'https://example-8188.proxy.runpod.net',
                                   'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'cors'}
                async with client.post('/prompt?test=1', headers=browser_headers, json={'test': 42}) as response:
                    assert response.status == 200
                    result = await response.json()
                    assert result['path'] == '/prompt?test=1'
                    assert json.loads(result['body']) == {'test': 42}
                assert (await client.post('/prompt', headers={**browser_headers,
                    'Origin': 'https://unrelated.example'}, json={'test': 42})).status == 403
                async with client.ws_connect('/ws?clientId=test', headers=AUTH) as ws:
                    await ws.send_str('progress')
                    assert (await asyncio.wait_for(ws.receive(), 2)).data == 'progress'
                    await ws.send_bytes(b'preview')
                    assert (await asyncio.wait_for(ws.receive(), 2)).data == b'preview'
        assert len(seen) == 2
        assert all('Authorization' not in headers for headers in seen)
        assert all('Origin' not in headers for headers in seen)
        assert all(not name.lower().startswith('sec-fetch-') for headers in seen for name in headers)
    asyncio.run(run())
