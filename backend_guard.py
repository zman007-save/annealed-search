"""Fail-closed ASGI boundary. Use one worker; never put its token in browser code."""
import asyncio
from collections import deque
import hmac
import json
import os
import time

class Guard:
    def __init__(self, app, token='', enabled=False, clock=time.monotonic):
        self.app, self.token, self.enabled, self.clock = app, token, enabled, clock
        self.recent, self.busy = deque(), False

    async def reply(self, send, status, message):
        body = json.dumps({'status': message}).encode()
        await send({'type':'http.response.start','status':status,'headers':[(b'content-type',b'application/json'),(b'cache-control',b'no-store')]})
        await send({'type':'http.response.body','body':body})

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            return await self.app(scope, receive, send)
        if scope['type'] != 'http':
            if scope['type'] == 'websocket':
                await send({'type':'websocket.close','code':1008})
            return
        path, method = scope.get('path'), scope.get('method')
        if path == '/healthz' and method == 'GET':
            return await self.reply(send, 200, 'alive')
        headers = scope.get('headers', [])
        auth = [v for k,v in headers if k.lower() == b'authorization']
        if len(self.token) < 32:
            return await self.reply(send, 503, 'not configured')
        expected = ('Bearer '+self.token).encode()
        if len(auth) != 1 or not hmac.compare_digest(auth[0], expected):
            return await self.reply(send, 401, 'unauthorized')
        if path == '/api/health' and method == 'GET':
            return await self.reply(send, 200, 'enabled' if self.enabled else 'provider calls disabled')
        if path != '/api/search' or method != 'POST':
            return await self.reply(send, 404, 'not found')
        if not self.enabled:
            return await self.reply(send, 503, 'provider calls disabled')
        if self.busy:
            return await self.reply(send, 429, 'one search already running')
        types = [v for k,v in headers if k.lower() == b'content-type']
        if len(types) != 1 or types[0].split(b';')[0].strip().lower() != b'application/json':
            return await self.reply(send, 415, 'JSON required')
        body = b''
        try:
            async def read_body():
                nonlocal body
                while True:
                    event = await receive()
                    if event['type'] != 'http.request':
                        raise ValueError()
                    body += event.get('body', b'')
                    if len(body) > 4096:
                        raise OverflowError()
                    if not event.get('more_body', False):
                        return
            await asyncio.wait_for(read_body(), timeout=5)
            data = json.loads(body)
            allowed = {'query','max_results','frequency_rounds','search_depth','meta_search','mantra','time_range','country','include_domains','exclude_domains'}
            if not isinstance(data,dict) or set(data)-allowed:
                raise ValueError()
            query = data.get('query')
            if not isinstance(query,str) or not 1 <= len(query.strip()) <= 180:
                raise ValueError()
            for name, default, maximum in [('max_results',5,10),('frequency_rounds',2,10)]:
                value = data.get(name,default)
                if type(value) is not int or not 1 <= value <= maximum:
                    raise ValueError()
                data[name] = value
            if type(data.get('meta_search',True)) is not bool:
                raise ValueError()
            data.setdefault('meta_search',True)
            if type(data.get('mantra',True)) is not bool:
                raise ValueError()
            if data.get('search_depth','basic') not in ('basic','advanced'):
                raise ValueError()
            data.setdefault('search_depth','basic')
            if data.get('time_range','any') not in ('any','day','week','month','year'):
                raise ValueError()
            for key in ('country','include_domains','exclude_domains'):
                if key in data and (not isinstance(data[key],str) or len(data[key]) > 300):
                    raise ValueError()
            data['query'] = query.strip()
        except OverflowError:
            return await self.reply(send,413,'request too large')
        except asyncio.TimeoutError:
            return await self.reply(send,408,'request timeout')
        except (ValueError,TypeError,UnicodeError):
            return await self.reply(send,400,'invalid request')
        # No await between accounting and reservation: atomic within one event loop.
        now=self.clock()
        while self.recent and self.recent[0] <= now-60:
            self.recent.popleft()
        if self.busy or len(self.recent) >= 2:
            return await self.reply(send,429,'search limit reached')
        self.recent.append(now)
        self.busy = True
        payload=json.dumps(data).encode()
        forwarded=False
        started=False
        async def replay():
            nonlocal forwarded
            if not forwarded:
                forwarded=True
                return {'type':'http.request','body':payload,'more_body':False}
            return await receive()
        async def safe_send(event):
            nonlocal started
            if event['type']=='http.response.start':
                started=True
                event={**event,'headers':[(k,v) for k,v in event.get('headers',[]) if k.lower()!=b'cache-control']+[(b'cache-control',b'no-store')]}
            await send(event)
        clean={**scope,'headers':[(k,v) for k,v in headers if k.lower() not in (b'authorization',b'content-length')]+[(b'content-length',str(len(payload)).encode())]}
        try:
            await self.app(clean,replay,safe_send)
        except Exception:
            if not started:
                await self.reply(send,502,'backend error')
            # Do not log exception messages, request bodies, or credentials.
        finally:
            self.busy=False

def configured_guard(app):
    return Guard(app, os.environ.get('BACKEND_ACCESS_TOKEN',''), os.environ.get('ENABLE_PROVIDER_CALLS','false').lower()=='true')
