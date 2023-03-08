
from pydoc import describe
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
import time
from langdetect import detect 
import numpy as np
from urllib.request import urlretrieve
from requests.models import PreparedRequest
from taxonerd import TaxoNERD
from pathlib import Path
import concurrent

from adept.config import INTERMEDIATE_DATA_DIR, logger, BHL_API_KEY
from adept.bhl.descriptions import BHLDetectDescriptions
from adept.tasks.descriptions.bhl.ocr import BHLOCRTask
from adept.tasks.base import BaseTask
from adept.utils.helpers import is_binomial
from adept.bhl.preprocess import BHLPreprocess


class BHLDescriptionTask(BaseTask):
    
    """
    Search BHL for a taxon            
    """

    taxon = luigi.Parameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'description'
    preprocess = BHLPreprocess() 
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        # Taxon for BHL must be a binomial
        if not is_binomial(self.taxon):
           raise luigi.parameter.ParameterException('Taxon for BHL must be a binomial - taxon parameter is {}'.format(self.taxon))
    
    def requires(self):        
       return BHLOCRTask(taxon=self.taxon)
            
    def run(self):
        data = []
        detect_descriptions = BHLDetectDescriptions(self.taxon)
        
        with self.input().open('r') as f:             
            ocr_text = yaml.full_load(f)
            logger.debug('BHLDescriptionTask: searching %s BHL pages for descriptions of %s', len(ocr_text), self.taxon)
            
            # Note: this is faster without using concurrent futures 
            for bhl_id, text in ocr_text.items():   
                # if not text: continue         
                if descriptions := detect_descriptions(text):
                    logger.debug('BHLDescriptionTask: %s descriptions detected in BHL page %s', len(descriptions), bhl_id)
                    data.append({                        
                        'source': f"bhl",
                        'source_id': bhl_id,
                        'taxon': self.taxon,
                        'text': '\n\n'.join(descriptions) 
                    })                   
        logger.debug('BHLDescriptionTask: %s descriptions detected for taxon %s', len(data), self.taxon)
        with self.output().open('w') as f:
            f.write(yaml.dump(data, explicit_start=True, default_flow_style=False))                 
                        
    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.yaml')  



    
if __name__ == "__main__":    
    import time
    start = time.time()       
    # luigi.build([BHLAggregateOCRTask(bhl_ids=l, taxon='Metopium toxiferum')], local_scheduler=True) 
    # luigi.build([BHLDescriptionTask(taxon='Metopium toxiferum')], local_scheduler=True)
    luigi.build([BHLDescriptionTask(taxon='Leersia hexandra', force=True)], local_scheduler=True)
    # luigi.build([BHLDescriptionTask(bhl_id=27274329, force=True)], local_scheduler=True) 
    stop = time.time()
    print(stop-start)             
    
