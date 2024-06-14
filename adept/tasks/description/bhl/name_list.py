
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
from adept.tasks.description.bhl import BHL_BASE_URL
from adept.traits import SimpleTraitTextClassifier

class BHLNameListTask(BaseExternalTask):
    
    taxon = luigi.Parameter()
    # https://www.biodiversitylibrary.org/namelistdownload/?type=c&name=Ancistrocladus_guineensis
    namelist_url = f'{BHL_BASE_URL}/namelistdownload'
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'name-list'
    api_endpoint = f'{BHL_BASE_URL}/api3'
    
    def run(self):

        # FIXME: Is there a SOLR instance
         
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

if __name__ == "__main__":    
    import time
    start = time.time()
    luigi.build([BHLNameListTask(taxon='Leersia hexandra', force=True)], local_scheduler=True)
    stop = time.time()
    print(stop-start)     