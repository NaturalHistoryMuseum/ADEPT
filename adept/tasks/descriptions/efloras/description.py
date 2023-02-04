import luigi
import enum
import yaml
from abc import ABCMeta, abstractmethod

from adept.config import INTERMEDIATE_DATA_DIR, logger
from adept.utils.soup import RequestSoup
from adept.utils.enum import Enum
from adept.traits import SimpleTraitTextClassifier
from adept.tasks.descriptions.base import BaseDescriptionTask
from adept.tasks.descriptions.efloras.search import EflorasSearchTask
from adept.tasks.descriptions.efloras import EFLORAS_BASE_URL


class EflorasDescriptionTask(BaseDescriptionTask, metaclass=ABCMeta):
    
    trait_classifier = SimpleTraitTextClassifier()
    
    class EFloras(enum.Enum, metaclass=Enum):
        FLORA_OF_NORTH_AMERICA = 1
        FLORA_OF_CHINA = 2            
        MOSS_FLORA_OF_CHINA = 4
        FLORA_OF_PAKISTAN = 5 
             
    @property
    @abstractmethod
    def flora_id(self):
        pass
    
    @property
    def source_name(self):
        return str(self.flora_id).lower()
    
    def requires(self):
        return EflorasSearchTask(taxon=self.taxon)    
            
    def get_taxon_description(self):
                            
        with self.input().open('r') as f:        
            search_results = yaml.full_load(f) 

        if not search_results:
            logger.info(f'No search results for {self.taxon} in efloras {self.flora_id}')
            return None

        taxon_id =  search_results.get(self.flora_id.value)
        if not taxon_id:
            logger.debug('No results for %s - %s', self.taxon, self.flora_id.value) 
            return None
           
        return self._parse_description(taxon_id)     
           
    def _parse_description(self, taxon_id):
                        
        url = f'{EFLORAS_BASE_URL}/florataxon.aspx'  
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
        return luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'efloras' / flora_name / f'{self.taxon}.yaml')           

class EflorasNorthAmericaDescriptionTask(EflorasDescriptionTask):
    
    flora_id = EflorasDescriptionTask.EFloras.FLORA_OF_NORTH_AMERICA
        
class EflorasChinaDescriptionTask(EflorasDescriptionTask):
    
    flora_id = EflorasDescriptionTask.EFloras.FLORA_OF_CHINA
        
class EflorasPakistanDescriptionTask(EflorasDescriptionTask):
    
    flora_id = EflorasDescriptionTask.EFloras.FLORA_OF_PAKISTAN  
    
class EflorasMossChinaDescriptionTask(EflorasDescriptionTask):
    
    flora_id = EflorasDescriptionTask.EFloras.MOSS_FLORA_OF_CHINA   

if __name__ == "__main__":    
    luigi.build([EflorasChinaDescriptionTask(taxon='Eleocharis palustris', force=True)], local_scheduler=True)  