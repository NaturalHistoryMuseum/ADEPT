
import luigi
import json
import re
import requests
import urllib
import enum
import yaml
import pandas as pd
import luigi
import logging
import pandas as pd
from langdetect import detect 
import numpy as np
from urllib.request import urlretrieve
from requests.models import PreparedRequest
from pathlib import Path

from adept.config import INTERMEDIATE_DATA_DIR, logger, BHL_API_KEY
from adept.tasks.base import BaseTask, BaseExternalTask
from adept.utils.request import CachedRequest
from adept.tasks.descriptions.bhl import BHL_BASE_URL
from adept.traits import SimpleTraitTextClassifier

class BHLNameListTask(BaseExternalTask):
    
    taxon = luigi.Parameter()
    # https://www.biodiversitylibrary.org/namelistdownload/?type=c&name=Ancistrocladus_guineensis
    namelist_url = f'{BHL_BASE_URL}/namelistdownload'
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'name-list'
    api_endpoint = f'{BHL_BASE_URL}/api3'
    
    def run(self):
        if taxon_name := self.search():            
            params = {
                'type': 'c',
                'name': self.encode_taxon(taxon_name)
            }
            req = PreparedRequest()
            req.prepare_url(self.namelist_url, params)               
            urlretrieve(req.url, self.output().path)
        else:
            # No results
            Path(self.output().path).touch()
            logger.error('No BHL search results for %s', self.taxon)

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.csv')   

    def search(self):
    
        params = {
            'op': 'NameSearch',
            'format': 'json',
            'apikey': BHL_API_KEY,
            'name': self.taxon
        } 
        
        r = CachedRequest(self.api_endpoint, params)
        result = r.json()
        # Check we have a result - but then use the taxon name as it's best match for CSV name list file
        if result['Result']:
            return self.taxon

    @staticmethod
    def encode_taxon(taxon):
        # BHL URL for CSV has underscores for spaces and $ for special chars
        # Artabotrys stenopetalus var. parviflorus => artabotrys_stenopetalus_var$_parviflorus     
        taxon = taxon.replace(' ', '_')
        taxon = re.sub(r'\W+', '$', taxon)
        return taxon


class BHLSearchTask(BaseTask):
    
    """
    Search BHL for a taxon            
    """
    
    taxon = luigi.Parameter()    
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'search'
    # Can change min_terms - lower = slower; higher = less images download but might miss
    trait_classifier = SimpleTraitTextClassifier(min_ratio=0.1, min_terms=25)
    
    def requires(self):        
        return BHLNameListTask(taxon=self.taxon) 
            
    def run(self):        
        with self.input().open('r') as f: 
            try:
                df = pd.read_csv(f)
            except pd.errors.EmptyDataError:
                logger.error('Empty BHL name list for %s', self.taxon)
                bhl_ids = []
            else:                
                logger.info('%s BHL pages located...filtering by language and trait term count', len(df.index))                 
                df['page_id'] = df['Url'].apply(lambda url: url.split('/')[-1])                
                # Filter out non-english pages
                df = df[df.Language == 'English']    
                # Filter out pages without any botanical trait terms in text                                   
                df['is_desc'] = df['page_id'].apply(self._is_description)
                df = df[df.is_desc == True]          
                logger.info('Writing %s search results (filtered by english and basic description classification) to file', len(df.index))                                   
                bhl_ids = df['page_id'].unique().tolist()    

        with self.output().open('w') as f:
            f.write(yaml.dump(bhl_ids, explicit_start=True, default_flow_style=False))             
                           
    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.en.yaml')              
            
        
    def _is_description(self, bhl_id):
        """
        So many results in BHL (some taxa, 1000s of pages), and most are irrelevant. 
        If we download and then OCR the image and then check for a description, this
        pipeline takes ages. 
        
        So use the BHL OCRd text with the simple text classier
        to determine if the page is worth including in the search results        
        """

        r = CachedRequest(f'https://www.biodiversitylibrary.org/pagetext/{bhl_id}')   
        return self.trait_classifier.is_description(r.text)             
    
if __name__ == "__main__":    
    luigi.build([BHLSearchTask(taxon='Leersia hexandra', force=True)], local_scheduler=True)      