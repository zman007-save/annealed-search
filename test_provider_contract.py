import asyncio, importlib, json, os, unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
import app
from provider_contract import ProviderFailure, provider_post, PUBLIC_PROFILE, bounded_payload, telem_options

class FakeClient:
 def __init__(self,code=200,empty=False):self.code=code;self.empty=empty;self.calls=[]
 async def __aenter__(self):return self
 async def __aexit__(self,*a):pass
 async def post(self,url,**kwargs):
  self.calls.append((url,kwargs))
  request=httpx.Request('POST',url)
  if self.code!=200:return httpx.Response(self.code,json={'error':'raw secret diagnostic'},request=request)
  if 'telem' in url:
   rows=[] if self.empty else [{'url':f'https://example{i}.test/article/news','title':f'Useful research discovery {i}','snippet':'science research'} for i in range(10)]
   return httpx.Response(200,json={'preprocessor_runs':[{'preprocessor_name':'brave','output_payload':{'results':rows}}]},request=request)
  if url.endswith('/search'):
   rows=[] if self.empty else [{'url':f'https://tavily{i}.test/article/research','title':f'Deep research publication {i}','content':'science research','score':.8} for i in range(5)]
   return httpx.Response(200,json={'results':rows},request=request)
  return httpx.Response(200,json={'results':[{'url':url,'raw_content':'science research evidence'} for url in kwargs['json']['urls']]},request=request)

def fake_anneal(articles):
 return {'redundancy':[{'max':0,'avg':0} for a in articles],'selected':list(range(len(articles))),'num_variables':len(articles),'num_couplings':0,'num_reads':100,'energy':-1,'trace':[-1],'converged':1}

class Contract(unittest.TestCase):
 def route(self,fake,payload=None,profile=PUBLIC_PROFILE):
  with patch.dict(os.environ,{'SEARCH_COST_PROFILE':profile}),patch.object(app,'TELEM_API_KEY','synthetic-telem'),patch.object(app,'TAVILY_API_KEY','synthetic-tavily'),patch.object(app,'make_client',return_value=fake),patch.object(app,'anneal',side_effect=fake_anneal),patch.object(app,'_record_dashboard_run') as recorder:
   with TestClient(app.app) as client:r=client.post('/api/search',json=payload or {'query':'science research'})
   return r,recorder.call_count
 def test_full_original_route_forces_bounded_profile(self):
  fake=FakeClient();r,logs=self.route(fake,{'query':'science research','frequency_rounds':40,'max_results':100,'meta_search':True,'search_depth':'advanced'})
  self.assertEqual(r.status_code,200);self.assertEqual(r.json()['status'],'completed');self.assertEqual(logs,0)
  search=[k['json'] for u,k in fake.calls if u.endswith('/search') and 'tavily' in u];self.assertEqual(len(search),1);self.assertEqual(search[0]['search_depth'],'basic');self.assertEqual(search[0]['max_results'],5)
  telem=[k['json'] for u,k in fake.calls if 'telem' in u][0];self.assertEqual(telem['search']['providers'],{'include':['brave']});self.assertEqual(telem['search']['tier'],'default')
  extracted=[u for endpoint,k in fake.calls if endpoint.endswith('/extract') for u in k['json']['urls']];self.assertLessEqual(len(extracted),5)
 def test_no_results_not_provider_failure(self):
  r,_=self.route(FakeClient(empty=True));self.assertEqual(r.status_code,200);self.assertEqual(r.json()['status'],'no_results');self.assertEqual(r.json()['articles'],[])
 def test_quota_propagates_to_http402(self):
  r,_=self.route(FakeClient(402));self.assertEqual(r.status_code,402);self.assertEqual(r.json()['error'],'provider_quota_exhausted');self.assertNotIn('raw secret',r.text)
 def test_rate_not_mislabeled_quota(self):
  r,_=self.route(FakeClient(429));self.assertEqual(r.status_code,429);self.assertEqual(r.json()['error'],'provider_rate_limited')
 def test_service_failure_not_empty_success(self):
  r,_=self.route(FakeClient(500));self.assertEqual(r.status_code,502);self.assertNotIn('articles',r.json())
 def test_credentials_error_sanitized(self):
  r,_=self.route(FakeClient(401));self.assertEqual(r.status_code,503);self.assertEqual(r.json()['error'],'provider_not_configured')
 def test_unknown_profile_no_calls(self):
  fake=FakeClient();r,_=self.route(fake,profile='mistyped');self.assertEqual(r.status_code,503);self.assertEqual(fake.calls,[])
 def test_default_original_profile_preserved(self):
  with patch.dict(os.environ,{'SEARCH_COST_PROFILE':''}):
   data={'query':'x','frequency_rounds':8};self.assertEqual(bounded_payload(data),data);self.assertNotIn('providers',telem_options(20))
 def test_tavily_error_contract_direct(self):
  with patch.object(app,'TAVILY_API_KEY','synthetic'):
   for method,args in [(app.tavily_search,('q',{})),(app.tavily_extract,(['https://a.test'],'q'))]:
    with self.assertRaises(ProviderFailure) as ctx:asyncio.run(method(FakeClient(402),*args))
    self.assertEqual(ctx.exception.code,'provider_quota_exhausted')
 def test_missing_key_failure(self):
  with patch.object(app,'TAVILY_API_KEY',''):
   with self.assertRaises(ProviderFailure):asyncio.run(app.tavily_search(FakeClient(),'q',{}))
 def test_timeout_sanitized(self):
  class TimeoutClient:
   async def post(self,*a,**k):raise httpx.ReadTimeout('secret-url')
  with self.assertRaises(ProviderFailure) as ctx:asyncio.run(provider_post(TimeoutClient(),'https://test',provider='telem',operation='search',expected='results'))
  self.assertEqual(ctx.exception.status,504);self.assertNotIn('secret',json.dumps(ctx.exception.public()))
 def test_malformed_response_not_empty(self):
  class Bad:
   async def post(self,*a,**k):return httpx.Response(200,json={'error':'secret'})
  with self.assertRaises(ProviderFailure):asyncio.run(provider_post(Bad(),'https://test',provider='tavily',operation='search',expected='results'))
if __name__=='__main__':unittest.main()
