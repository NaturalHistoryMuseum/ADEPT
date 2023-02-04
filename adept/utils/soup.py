import requests
import requests_cache
from bs4 import BeautifulSoup

from adept.config import CACHE_DIR, logger
from adept.utils.request import CachedRequest



class Soup(): 
    
    parser = 'html5lib'   
    
    def __init__(self, text: str):
        self._markup = self._to_soup(text)
    
    def _to_soup(self, text: str):
        return BeautifulSoup(text, features=self.parser)  

    @property
    def markup(self):
        return self._markup  


class RequestSoup(Soup):
          
    def __init__(self, url, **params):        
        self.url = url
        self.params = params
        self._markup = self.parse()        
        
    def parse(self):        
        logger.debug(self.parametised_url)
        request = CachedRequest(self.url, params=self.params)
        return self._to_soup(request.text)  

    @property
    def parametised_url(self):
        url = f'{self.url}?' + '&'.join([f'{k}={{{k}}}' for k in self.params.keys()])
        return url.format(**self.params)    
    
if __name__ == '__main__':  
    
    s = Soup('')
    
    s.markup.find()
    
    
    
