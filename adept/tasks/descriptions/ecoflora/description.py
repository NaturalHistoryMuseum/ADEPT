import luigi
import json
import re
import requests
import urllib

from adept.config import INTERMEDIATE_DATA_DIR, logger
from adept.utils.soup import RequestSoup
from adept.tasks.descriptions.base import BaseDescriptionTask
from adept.tasks.descriptions.ecoflora import ECOFLORAS_BASE_URL
from adept.tasks.descriptions.ecoflora.index import EcofloraIndexTask

class EcofloraDescriptionTask(BaseDescriptionTask):
    
    taxon = luigi.Parameter()      
    source_name = 'ecoflora'

    def requires(self):
        return EcofloraIndexTask()    
            
    def get_taxon_description(self):
        
        with self.input().open('r') as f:        
            taxa_index = json.load(f)
                                
        try:
            taxon_no = taxa_index[self.taxon]
        except KeyError:
            logger.info('Taxon %s not found in the EcoFLora taxa index', self.taxon)
        else:            
            return self._parse_description(taxon_no)
            
    def _parse_description(self, taxon_no):
        
        url =  f'{ECOFLORAS_BASE_URL}/info/{taxon_no}.html'
        try:
            soup = RequestSoup(url)
        except requests.exceptions.RequestException:
            return
        
        if div := soup.markup.find('div', {"class": "description"}):
            # Remove the attribution para .e.g C.T.W., A.M. , C.S., B.F.
            # By ensuring the line has some lower case characters               
            ps = [p for p in div.findAll('p') if bool(re.search(r"[a-z]", p.text))]
            description = ' '.join([p.text for p in ps])
            return description
        
            
    def output(self):
        return luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'ecoflora' / f'{self.taxon}.yaml')    
    
if __name__ == "__main__":    
    luigi.build([EcofloraDescriptionTask(taxon='Eleocharis palustris', force=True)], local_scheduler=True)     