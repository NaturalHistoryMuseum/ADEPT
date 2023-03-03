
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
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed

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
         
        params = {
            'type': 'c',
            'name': self.encode_taxon(self.taxon)
        }
        req = PreparedRequest()
        req.prepare_url(self.namelist_url, params)               
        urlretrieve(req.url, self.output().path)
        # No results
        # Path(self.output().path).touch()
        # logger.error('No BHL search results for %s', self.taxon)

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.csv')   

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
    # Can change min_terms - lower = slower; higher = less images download but might miss some
    trait_classifier = SimpleTraitTextClassifier(min_terms=15, min_chars=2500)
    
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
                df['page_id'] = df['Url'].apply(lambda url: int(url.split('/')[-1]))    
                df = df.set_index('page_id')  
                # Filter out non-english pages
                df = df[df.Language == 'English']                   
                # df = df.head(100)        

                text = self.get_text(df.index.to_list())
                df["text"] = df.index.map(text) 
                # Filter out pages without any botanical trait terms in text                                   
                df['is_desc'] = df['text'].apply(self._is_description)
                df = df[df.is_desc == True]          
                logger.info('Writing %s search results (filtered by english and basic description classification) to file', len(df.index))                                   
                bhl_ids = df.index.tolist()    

        with self.output().open('w') as f:
            f.write(yaml.dump(bhl_ids, explicit_start=True, default_flow_style=False))             
                           
    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.en.yaml')              
            
    @staticmethod
    def get_text(page_ids):                
        # https://morioh.com/p/f9705e6b524b
        with FuturesSession(max_workers=20, session=CachedRequest.session) as session:
            def _future(page_id):
                future = session.get(f'https://www.biodiversitylibrary.org/pagetext/{page_id}')
                future.page_id = page_id
                return future

            futures=[_future(page_id) for page_id in page_ids]    
            text = {int(future.page_id): future.result().text for future in as_completed(futures)}
            return text
    
    def _is_description(self, text):
        """
        So many results in BHL (some taxa, 1000s of pages), and most are irrelevant. 
        If we download and then OCR the image and then check for a description, this
        pipeline takes ages. 
        
        So use the BHL OCRd text with the simple text classier
        to determine if the page is worth including in the search results        
        """
        return self.trait_classifier.is_description(text) 
    
if __name__ == "__main__":    
    import time
    start = time.time()
    luigi.build([BHLSearchTask(taxon='Leersia hexandra', force=True)], local_scheduler=True)
    stop = time.time()
    print(stop-start)          