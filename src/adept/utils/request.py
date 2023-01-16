import requests
from requests_cache import CachedSession
import http.client


from adept.config import CACHE_DIR

# https://stackoverflow.com/questions/62599036/python-requests-is-slow-and-takes-very-long-to-complete-http-or-https-request
http.client.HTTPConnection.debuglevel = 1


class CachedRequest():
    
    cached_request = CachedSession(
        CACHE_DIR / '.requests',
         # Cache 400 responses so we don't keep retrying them
        allowable_codes=[200, 400, 404],       
    )
    
    timeout = 5
    encoding = 'utf-8'
    raw_chunked = True
    
    def __init__(self, url, params=None):  
        # self._r = requests.get(url, params=params)
        self._r = self.cached_request.get(url, params=params, timeout=self.timeout)
        self._r.raw.chunked = self.raw_chunked
        self._r.encoding = self.encoding       
        self._r.raise_for_status()        
        
    def json(self):
        return self._r.json()
    
    @property
    def text(self):
        return self._r.text   