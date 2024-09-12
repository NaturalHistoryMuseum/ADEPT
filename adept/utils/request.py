import requests
from requests_cache import CachedSession, RedisCache
import http.client


from adept.config import CACHE_DIR

class CachedRequest():

    backend = RedisCache(host='localhost')
    
    session = CachedSession(
        CACHE_DIR / '.requests',
        backend=backend,
         # Cache 400 responses so we don't keep retrying them
        allowable_codes=[200, 400, 404],       
    )
    
    timeout = 30
    encoding = 'utf-8'
    raw_chunked = True
    
    def __init__(self, url, params=None):  
        # self._r = requests.get(url, params=params)
        self._r = self.session.get(url, params=params, timeout=self.timeout)
        self._r.raw.chunked = self.raw_chunked
        self._r.encoding = self.encoding       
        self._r.raise_for_status()        
        
    def json(self):
        return self._r.json()
    
    @property
    def text(self):
        return self._r.text   
    
    @property
    def content(self):
        return self._r.content     