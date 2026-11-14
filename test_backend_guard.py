import asyncio,json,unittest
from backend_guard import Guard
TOKEN='offline-test-placeholder-'+'x'*32
class Tests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.calls=[]
        self.now=100
        async def downstream(scope,receive,send):
            self.calls.append((scope,json.loads((await receive())['body'])))
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'{"ok":true}'})
        self.guard=Guard(downstream,TOKEN,True,lambda:self.now)
    async def request(self,data=None,path='/api/search',method='POST',headers=None,raw=None):
        scope={'type':'http','path':path,'method':method,'headers':headers if headers is not None else [(b'authorization',('Bearer '+TOKEN).encode()),(b'content-type',b'application/json')]}
        body=raw if raw is not None else json.dumps(data if data is not None else {'query':'safe offline fixture'}).encode()
        async def receive():return {'type':'http.request','body':body,'more_body':False}
        sent=[]
        await self.guard(scope,receive,sent.append_async if False else self.collect(sent))
        return sent[0]['status'],sent
    def collect(self,sent):
        async def send(e):sent.append(e)
        return send
    async def test_defaults_and_token_stripped(self):
        self.assertEqual((await self.request())[0],200)
        s,d=self.calls[0];self.assertNotIn(b'authorization',dict(s['headers']))
        self.assertEqual((d['max_results'],d['frequency_rounds'],d['meta_search'],d['search_depth']),(5,1,False,'basic'))
    async def test_missing_token(self):
        self.assertEqual((await self.request(headers=[]))[0],401);self.assertEqual(self.calls,[])
    async def test_duplicate_token(self):
        h=[(b'authorization',('Bearer '+TOKEN).encode())]*2
        self.assertEqual((await self.request(headers=h))[0],401)
    async def test_unconfigured(self):
        self.guard.token='short';self.assertEqual((await self.request())[0],503)
    async def test_default_disabled(self):
        self.guard.enabled=False;self.assertEqual((await self.request())[0],503);self.assertFalse(self.calls)
    async def test_liveness_no_auth(self):
        self.assertEqual((await self.request(path='/healthz',method='GET',headers=[]))[0],200);self.assertFalse(self.calls)
    async def test_health_no_provider(self):
        self.assertEqual((await self.request(path='/api/health',method='GET'))[0],200);self.assertFalse(self.calls)
    async def test_no_docs_or_static(self):
        for p in ['/','/docs','/openapi.json','/static/index.html']:
            self.assertEqual((await self.request(path=p,method='GET'))[0],404)
    async def test_wrong_method(self):self.assertEqual((await self.request(method='GET'))[0],404)
    async def test_malformed(self):
        for b in [b'null',b'[]',b'{',b'\xff']:
            self.assertEqual((await self.request(raw=b))[0],400)
    async def test_body_cap(self):self.assertEqual((await self.request(raw=b'x'*4097))[0],413)
    async def test_type(self):self.assertEqual((await self.request(headers=[(b'authorization',('Bearer '+TOKEN).encode())]))[0],415)
    async def test_payload_bounds(self):
        for d in [{'query':''},{'query':'x'*181},{'query':4},{'query':'x','frequency_rounds':3},{'query':'x','max_results':11},{'query':'x','max_results':True},{'query':'x','meta_search':True},{'query':'x','search_depth':'premium'},{'query':'x','unknown':'x'},{'query':'x','time_range':'all'},{'query':'x','country':[]},{'query':'x','mantra':1}]:
            self.assertEqual((await self.request(d))[0],400,d)
        self.assertFalse(self.calls)
    async def test_rate(self):
        self.assertEqual((await self.request())[0],200);self.assertEqual((await self.request())[0],200)
        self.assertEqual((await self.request())[0],429);self.now+=61
        self.assertEqual((await self.request())[0],200)
    async def test_total_limit(self):
        for _ in range(10):
            self.now+=61;self.assertEqual((await self.request())[0],200)
        self.now+=61;self.assertEqual((await self.request())[0],429)
    async def test_concurrency(self):
        enter,release=asyncio.Event(),asyncio.Event()
        original=self.guard.app
        async def slow(*args):enter.set();await release.wait();await original(*args)
        self.guard.app=slow
        task=asyncio.create_task(self.request());await enter.wait()
        self.assertEqual((await self.request())[0],429);release.set();self.assertEqual((await task)[0],200)
    async def test_error_redacted_and_busy_released(self):
        async def bad(*a):raise RuntimeError(TOKEN)
        self.guard.app=bad
        status,events=await self.request();self.assertEqual(status,502)
        self.assertNotIn(TOKEN,str(events));self.assertFalse(self.guard.busy)
    async def test_chunked_size_cap(self):
        events=iter([{'type':'http.request','body':b'x'*3000,'more_body':True},{'type':'http.request','body':b'x'*2000}])
        async def receive():return next(events)
        sent=[]
        await self.guard({'type':'http','path':'/api/search','method':'POST','headers':[(b'authorization',('Bearer '+TOKEN).encode()),(b'content-type',b'application/json')]},receive,self.collect(sent))
        self.assertEqual(sent[0]['status'],413)
if __name__=='__main__':unittest.main()
