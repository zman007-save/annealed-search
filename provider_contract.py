"""Server-only provider contract. All tests use fake HTTP transports."""
import os
import httpx

PUBLIC_PROFILE = 'public_brave_basic_v1'
class ProviderFailure(Exception):
    def __init__(self, provider, operation, code, status):
        self.provider, self.operation, self.code, self.status = provider, operation, code, status
        super().__init__(code)
    def public(self):
        messages = {
          'provider_quota_exhausted':'A search provider reports insufficient credits. Search is paused.',
          'provider_rate_limited':'A search provider is temporarily rate limited. Please try later.',
          'provider_unavailable':'A search provider is unavailable. No fallback search was substituted.',
          'provider_timeout':'The search provider timed out. The outcome requires review before retrying.',
          'provider_not_configured':'The original search service is not configured yet.',
          'provider_invalid_response':'The provider response could not be verified.',
        }
        return {'error':self.code,'message':messages[self.code],'provider':self.provider,'operation':self.operation,'status':'failed'}

async def provider_post(client, url, *, provider, operation, expected, **kwargs):
    try:
        response = await client.post(url, **kwargs)
    except httpx.TimeoutException:
        raise ProviderFailure(provider,operation,'provider_timeout',504) from None
    except httpx.RequestError:
        raise ProviderFailure(provider,operation,'provider_unavailable',502) from None
    code=response.status_code
    if code==402: raise ProviderFailure(provider,operation,'provider_quota_exhausted',402)
    if code==429: raise ProviderFailure(provider,operation,'provider_rate_limited',429)
    if code in (401,403): raise ProviderFailure(provider,operation,'provider_not_configured',503)
    if code>=400: raise ProviderFailure(provider,operation,'provider_unavailable',502)
    try:
        data=response.json()
        if not isinstance(data,dict) or data.get('error') or not isinstance(data.get(expected),list):
            raise ValueError()
    except (ValueError,TypeError):
        raise ProviderFailure(provider,operation,'provider_invalid_response',502) from None
    return data

def public_profile():
    value=os.environ.get('SEARCH_COST_PROFILE','')
    if not value: return None
    if value!=PUBLIC_PROFILE: raise ProviderFailure('pipeline','configuration','provider_not_configured',503)
    # This is explicit deployment configuration, never a request parameter.
    # Must remain unset until account pricing/credits and this endpoint profile are verified.
    return PUBLIC_PROFILE

def bounded_payload(payload):
    if public_profile():
        return {'query':payload.get('query',''),'frequency_rounds':1,'max_results':5,'search_depth':'basic','meta_search':False,'mantra':True}
    return payload

def telem_options(num_results):
    if public_profile():
        # Explicit allowlist preserves Telem routing but prevents unrestricted fanout.
        return {'num_results':5,'tier':'default','auto_routing':'accuracy','providers':{'include':['brave']}}
    return {'num_results':num_results,'tier':'extended','auto_routing':'accuracy'}

def extract_limit():
    return 5 if public_profile() else 40
