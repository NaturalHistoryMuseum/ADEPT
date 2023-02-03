
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

from adept.config import INTERMEDIATE_DATA_DIR, logger, BHL_API_KEY
from adept.tasks.base import BaseTask, BaseExternalTask
from adept.utils.request import CachedRequest
from adept.tasks.descriptions.bhl import BHL_BASE_URL


class BHLNameListTask(BaseExternalTask):
    
    taxon = luigi.Parameter()
    # https://www.biodiversitylibrary.org/namelistdownload/?type=c&name=Ancistrocladus_guineensis
    base_url = f'{BHL_BASE_URL}/namelistdownload'
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'name-list'
    
    def run(self):
        params = {
            'type': 'c',
            'name': self.encoded_taxon
        }
        req = PreparedRequest()
        req.prepare_url(self.base_url, params)        
        urlretrieve(req.url, self.output().path)

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.encoded_taxon}.csv')   

    @property
    def encoded_taxon(self):
        # BHL URL for CSV has underscores for spaces and $ for special chars
        # Artabotrys stenopetalus var. parviflorus => artabotrys_stenopetalus_var$_parviflorus     
        taxon = self.taxon.replace(' ', '_')
        taxon = re.sub(r'\W+', '$', taxon)
        return taxon


class BHLSearchTask(BaseTask):
    
    """
    Search BHL for a taxon            
    """
    
    taxon = luigi.Parameter()
    endpoint = f'{BHL_BASE_URL}/api3'
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'search'
    
    def requires(self):        
        if taxon_name := self._search():
            return BHLNameListTask(taxon=taxon_name) 
        else: 
            logger.warning('No results for %s in efloras', self.taxon)
            
    def run(self):
        with self.input().open('r') as f: 
            df = pd.read_csv(f)
            
            df['page_id'] = df['Url'].apply(lambda url: url.split('/')[-1])
            # Detect english language title - BHL Language isn't always set correctly
            df['detected_lang'] = df.Title.apply(self._detect_language)
            # Filter out not endlish languages
            df = df[(df['detected_lang'] == 'en') | (df.Language == 'English')]              
            df.to_csv(self.output().path)
                           
    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.en.csv')              
            
    @staticmethod 
    def _detect_language(title):
        try:
            return detect(title)
        except:
            return np.nan               
            
    def _search(self):
    
        params = {
            'op': 'NameSearch',
            'format': 'json',
            'apikey': BHL_API_KEY,
            'name': self.taxon
        } 
        
        r = CachedRequest(self.endpoint, params)
        result = r.json()
        if result['Result']:
            return result['Result'][0]['NameConfirmed']

    

    
if __name__ == "__main__":    
    luigi.build([BHLSearchTask(taxon='Metopium toxiferum')], local_scheduler=True)      