import luigi
import json
import re
import requests
import urllib

from adept.config import INTERMEDIATE_DATA_DIR, logger
from adept.utils.soup import RequestSoup
from adept.tasks.descriptions.ecoflora import ECOFLORAS_BASE_URL


class EcofloraIndexTask(luigi.ExternalTask):
    
    """
    Build index of ecoflora taxonomy
    """

    def run(self):
        results = self._parse_search()  
        
        with self.output().open('w') as f: 
            f.write(json.dumps(results))
            
    def _parse_search(self):
        # Search page returns a list of all taxa if no parameter is supplied         
        soup = RequestSoup(f'{ECOFLORAS_BASE_URL}/search_synonyms.php')
        links = soup.markup.find_all('a', {'href': re.compile(r'.*search_species2.php\?plant_no=.*')})
        
        results = {}

        for link in links:
            parsed_url = urllib.parse.urlparse(link.get('href'))
            qs = urllib.parse.parse_qs(parsed_url.query)            
            results[link.text.strip()] = qs['plant_no'][0]
            
        return results
            
    def output(self):
        return luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'ecoflora' / 'index.json')     


 