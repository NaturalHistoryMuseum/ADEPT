import luigi
import json
import re
import requests
import urllib
import enum
import yaml
from abc import ABCMeta, abstractmethod

from adept.config import INTERMEDIATE_DATA_DIR, logger
from adept.utils.soup import RequestSoup
from adept.tasks.description.efloras import EFLORAS_BASE_URL


class EflorasSearchTask(luigi.ExternalTask):
    
    """
    Search efloras for a taxon    
    We set flora_id = 0 to return all floras            
    """
    
    taxon = luigi.Parameter()

    def run(self):
        results = self._search()  
        
        if not results:
            logger.warning('No results for %s in efloras', self.taxon)
                                
        with self.output().open('w') as f: 
            # NB: We use YAML as JSON doesn't support int keys
            yaml.dump(results, f)
            
    def _search(self):
    
        url =  f'{EFLORAS_BASE_URL}/browse.aspx'

        try:
            # We use flora_id = 0 to search for all, which is 
            # then cached for all floras - too slow otherwise
            soup = RequestSoup(url, flora_id=0, name_str=self.taxon)
        except requests.exceptions.RequestException as e:
            logger.error(e)
            return None   
                
        return self._parse_search_page(soup)
    
    def _parse_search_page(self, soup):
        
        search_results = {}
        
        title_span = soup.markup.find("span", {"id": "ucFloraTaxonList_lblListTitle"}) 
        
        if title_span.get_text(strip=True) == 'No taxa found':
            logger.info('No taxa found: %s', soup.parametised_url)
            return {}
        
        div = soup.markup.find("div", {"id": "ucFloraTaxonList_panelTaxonList"})        
        
        # We specify title="Accepted name" to exclude synonyms
        for a in div.find_all("a", href=re.compile("^florataxon"), title="Accepted Name"):        
            parsed_url = urllib.parse.urlparse(a.get('href'))
            qs = urllib.parse.parse_qs(parsed_url.query) 
            search_results[int(qs['flora_id'][0])] = int(qs['taxon_id'][0]) 
        
        return search_results    

            
    def output(self):
        return luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'efloras' / 'search' / f'{self.taxon}.yaml')   