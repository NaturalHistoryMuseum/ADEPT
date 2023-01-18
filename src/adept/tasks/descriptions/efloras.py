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
from adept.utils.enum import Enum
from adept.traits import SimpleTraitTextClassifier
from adept.tasks.descriptions.description import DescriptionTask


class EflorasSearchTask(luigi.ExternalTask):
    
    """
    Search efloras for a taxon    
    We set flora_id = 0 to return all floras            
    """
    
    taxon = luigi.Parameter()
    base_url = 'http://efloras.org'

    def run(self):
        results = self._search()  
        
        if not results:
            logger.warning('No results for %s in efloras', self.taxon)
                                
        with self.output().open('w') as f: 
            # NB: We use YAML as JSON doesn't support int keys
            yaml.dump(results, f)
            
    def _search(self):
    
        url =  f'{self.base_url}/browse.aspx'

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


class EcofloraDescriptionTask(DescriptionTask, metaclass=ABCMeta):
    
    taxon = luigi.Parameter()
    base_url = 'http://efloras.org'
    trait_classifier = SimpleTraitTextClassifier()
    
    class Floras(enum.Enum, metaclass=Enum):
        FLORA_OF_NORTH_AMERICA = 1
        FLORA_OF_CHINA = 2            
        MOSS_FLORA_OF_CHINA = 4
        FLORA_OF_PAKISTAN = 5 
             
    @property
    @abstractmethod
    def flora_id(self):
        pass     
    
    def requires(self):
        return EflorasSearchTask(taxon=self.taxon)    
            
    def get_taxon_description(self):
                    
        with self.input().open('r') as f:        
            search_results = yaml.full_load(f) 
            
        if not search_results:
            return None

        taxon_id =  search_results.get(self.flora_id.value)
        if not taxon_id:
            logger.debug('No results for %s - %s', self.taxon, self.flora_id.value) 
            return None
           
        return self._parse_description(taxon_id)     
           
    def _parse_description(self, taxon_id):
                        
        url = f'{self.base_url}/florataxon.aspx'  
        try:      
            soup = RequestSoup(url, flora_id=self.flora_id.value, taxon_id=taxon_id)
        except Exception as e:
            logger.error('Requests exception: %s', e)
            return
        
        taxon_treatment = soup.markup.find('div', {'id': 'panelTaxonTreatment'})   
        
        if not taxon_treatment:
            logger.error('No taxon treatment: %s', soup.parametised_url) 
            return          
        
        p_text = [p.get_text() for p in taxon_treatment.find_all('p') if p.get_text(strip=True) and not p.find('table')]        
        descriptions = [p for p in p_text if self.trait_classifier.is_description(p)]

        if descriptions:
            if len(descriptions) > 1:
                logger.debug('Multiple treatment paragraphs %s', soup.parametised_url)
                
            return '\n'.join(descriptions)        
          
    def output(self):
        flora_name = self.flora_id.name.lower()
        return luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'efloras' / flora_name / f'{self.taxon}.txt')           

class EflorasNorthAmericaDescriptionTask(EcofloraDescriptionTask):
    
    flora_id = EcofloraDescriptionTask.Floras.FLORA_OF_NORTH_AMERICA
        
class EflorasChinaDescriptionTask(EcofloraDescriptionTask):
    
    flora_id = EcofloraDescriptionTask.Floras.FLORA_OF_CHINA
        
class EflorasPakistanDescriptionTask(EcofloraDescriptionTask):
    
    flora_id = EcofloraDescriptionTask.Floras.FLORA_OF_PAKISTAN  
    
class EflorasMossChinaDescriptionTask(EcofloraDescriptionTask):
    
    flora_id = EcofloraDescriptionTask.Floras.MOSS_FLORA_OF_CHINA   

if __name__ == "__main__":    
    luigi.build([EflorasChinaDescriptionTask(taxon='Metopium toxiferum', force=True)], local_scheduler=True)  