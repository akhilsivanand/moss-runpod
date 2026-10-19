"""Authenticated ComfyUI gateway with preparation and readiness pages."""
import asyncio
import base64
import hmac
import html
import ipaddress
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit, quote

import aiohttp
from aiohttp import web

HOP_HEADERS = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
               'te', 'trailer', 'transfer-encoding', 'upgrade', 'host', 'authorization'}
UPSTREAM_SESSION = web.AppKey('upstream', aiohttp.ClientSession)


def normalize_origin(value):
    """Parse a single HTTP Origin without trusting forwarded request headers."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        return None
    if ('?' in value or '#' in value
            or any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value)):
        return None
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.path or parsed.query or parsed.fragment):
            return None
        host = parsed.hostname.encode('idna').decode('ascii').lower()
        if '%' in host or parsed.netloc.endswith(':'):
            return None
        try:
            host = ipaddress.ip_address(host).compressed.lower()
        except ValueError:
            if len(host) > 253 or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', part)
                                         for part in host.split('.')):
                return None
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == 'https' else 80
        if port < 1:
            return None
        return parsed.scheme, host, port
    except (ValueError, UnicodeError):
        return None


def public_origin_from_environment():
    configured = os.environ.get('MOSS_PUBLIC_ORIGIN')
    if configured is not None:
        origin = normalize_origin(configured)
        if origin is None:
            raise ValueError('MOSS_PUBLIC_ORIGIN must be an HTTP(S) origin without a path, query, or credentials.')
        return origin
    pod_id = os.environ.get('RUNPOD_POD_ID')
    if pod_id is not None:
        if not re.fullmatch(r'[a-z0-9]{8,58}', pod_id):
            raise ValueError('RUNPOD_POD_ID is not a valid Pod identifier.')
        return normalize_origin('https://' + pod_id + '-8188.proxy.runpod.net')
    return None


def origin_allowed(origin, request_host, public_origin):
    if origin is None:
        return True  # Authenticated API clients need not send a browser Origin.
    normalized = normalize_origin(origin)
    if normalized is None:
        return False
    if public_origin is not None:
        return normalized == public_origin
    # Direct/local use, or a proxy preserving the public Host. TLS may terminate
    # before this gateway, so the request's internal HTTP scheme is not public.
    expected = normalize_origin(normalized[0] + '://' + request_host)
    return normalized == expected


def authorized(header, password):
    try:
        scheme, encoded = header.split(' ', 1)
        if scheme.lower() != 'basic':
            return False
        decoded = base64.b64decode(encoded, validate=True).decode('utf-8')
        username, secret = decoded.split(':', 1)
        return hmac.compare_digest(username.encode('utf-8'), b'moss') and hmac.compare_digest(secret.encode('utf-8'), password.encode('utf-8'))
    except (ValueError, UnicodeError):
        return False


def page(state, workflow_config):
    ready = state.get('ready', False)
    cards = []
    if ready:
        entries = list(workflow_config['presets'].values()) + list(workflow_config.get('ui_only', {}).values())
        for entry in entries:
            name = Path(entry['ui']).stem
            href = '/?template=' + quote(name) + '&source=moss'
            cards.append(f'<a class="card" href="{html.escape(href)}">{html.escape(entry["title"])}<span>Open workflow →</span></a>')
    detail = 'Choose a workflow to open it in ComfyUI.' if ready else state.get('detail', 'Preparing your workspace…')
    phase = 'Ready' if ready else state.get('phase', 'Starting').replace('_', ' ').title()
    refresh = '' if ready else '<meta http-equiv="refresh" content="5">'
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{refresh}<title>MOSS Image Studio</title>
<style>body{{margin:0;background:#101815;color:#eef4ed;font:17px system-ui,sans-serif}}main{{max-width:900px;margin:10vh auto;padding:28px}}.label{{color:#a4cdb0;letter-spacing:.12em;font-size:13px}}h1{{font-size:clamp(36px,6vw,62px);font-weight:550;letter-spacing:-.04em;margin:16px 0}}p{{line-height:1.6;color:#c3cec5}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:36px}}.card{{padding:25px;background:#1b2922;border:1px solid #344a3c;border-radius:12px;color:#fff;text-decoration:none}}.card:hover{{border-color:#a4cdb0}}.card span{{display:block;color:#a4cdb0;margin-top:22px;font-size:14px}}.editor{{display:inline-block;color:#b7d7bf;margin-top:28px}}.status{{color:#a4cdb0}}</style>
<main><div class="label">MOSS IMAGE STUDIO</div><h1>Your next image starts here.</h1><div class="status">{html.escape(phase)}</div><p>{html.escape(detail)}</p><div class="grid">{''.join(cards)}</div>
{'<a class="editor" href="/?editor=1">Continue in your ComfyUI workspace →</a>' if ready else '<p>This page refreshes automatically. The first start downloads the models; later starts reuse them.</p>'}</main></html>'''


def create_app(state, root, password, mode='pod', upstream='http://127.0.0.1:8189'):
    config = json.loads((Path(root) / 'config/workflows.json').read_text())
    public_origin = public_origin_from_environment() if mode == 'pod' else None
    app = web.Application(client_max_size=50 * 1024**2)

    async def session_context(application):
        application[UPSTREAM_SESSION] = aiohttp.ClientSession(auto_decompress=False,
            timeout=aiohttp.ClientTimeout(total=None, sock_connect=15))
        yield
        await application[UPSTREAM_SESSION].close()

    app.cleanup_ctx.append(session_context)

    async def dispatch(request):
        if request.path in ('/healthz', '/readyz', '/ping'):
            if request.method != 'GET':
                raise web.HTTPMethodNotAllowed(request.method, ['GET'])
            ready = bool(state.get('ready'))
            if request.path == '/ping':
                return web.Response(status=200 if ready else 204)
            code = 200 if request.path == '/healthz' or ready else 503
            return web.json_response({'ready': ready, 'phase': state.get('phase', 'starting')}, status=code)
        if mode != 'pod':
            raise web.HTTPNotFound()
        if not authorized(request.headers.get('Authorization', ''), password):
            return web.Response(status=401, text='Sign in with username moss and your MOSS_PASSWORD.',
                headers={'WWW-Authenticate': 'Basic realm="MOSS Image Studio", charset="UTF-8"',
                         'Cache-Control': 'no-store'})
        origin = request.headers.get('Origin')
        if not origin_allowed(origin, request.host, public_origin):
            raise web.HTTPForbidden(text='Cross-origin requests are not allowed.')
        if request.path == '/moss/status':
            return web.json_response({k: state.get(k) for k in ('phase', 'detail', 'ready', 'bytes_total', 'bytes_complete')},
                                     headers={'Cache-Control': 'no-store'})
        if not state.get('ready') or (request.path == '/' and not any(k in request.query for k in ('template', 'editor'))):
            if request.method != 'GET':
                return web.json_response({'error': 'Model preparation is still in progress.'}, status=503)
            return web.Response(text=page(state, config), content_type='text/html', headers={'Cache-Control': 'no-store'})
        target = upstream.rstrip('/') + str(request.rel_url)
        session = request.app[UPSTREAM_SESSION]
        if request.headers.get('Upgrade', '').lower() == 'websocket':
            server = await session.ws_connect(target, max_msg_size=64 * 1024**2)
            browser = web.WebSocketResponse(max_msg_size=64 * 1024**2)
            await browser.prepare(request)

            async def pump(source, destination):
                async for message in source:
                    if message.type == aiohttp.WSMsgType.TEXT:
                        await destination.send_str(message.data)
                    elif message.type == aiohttp.WSMsgType.BINARY:
                        await destination.send_bytes(message.data)
                    elif message.type == aiohttp.WSMsgType.ERROR:
                        break
            tasks = [asyncio.create_task(pump(server, browser)), asyncio.create_task(pump(browser, server))]
            try:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                await server.close()
                await browser.close()
            return browser
        # Browser origin checks belong at this authenticated public boundary.
        # ComfyUI's loopback origin guard would reject the public browser origin
        # after the proxy replaces Host with its private upstream address.
        headers = {k: v for k, v in request.headers.items()
                   if k.lower() not in HOP_HEADERS and k.lower() != 'origin'
                   and not k.lower().startswith('sec-fetch-')}
        async with session.request(request.method, target, headers=headers, data=request.content,
                                   allow_redirects=False) as response:
            outgoing = web.StreamResponse(status=response.status,
                headers={k: v for k, v in response.headers.items() if k.lower() not in HOP_HEADERS})
            await outgoing.prepare(request)
            async for chunk in response.content.iter_chunked(64 * 1024):
                await outgoing.write(chunk)
            await outgoing.write_eof()
            return outgoing

    app.router.add_route('*', '/{path:.*}', dispatch)
    return app
