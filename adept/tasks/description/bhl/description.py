
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
from abc import ABCMeta, abstractmethod

from adept.config import INTERMEDIATE_DATA_DIR, logger
from adept.bhl.descriptions import BHLDetectDescriptions
from adept.tasks.description.bhl.search import BHLSearchTask
from adept.tasks.base import BaseTask
from adept.tasks.description.bhl.tesseract import BHLTesseractOCRTask
from adept.utils.helpers import is_binomial
# from adept.bhl.preprocess import BHLPreprocess

    
class BHLDescriptionBaseTask(BaseTask, metaclass=ABCMeta):
    taxon = luigi.Parameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'description'
    # FIXME: Not used??
    # preprocess = BHLPreprocess() 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        # Taxon for BHL must be a binomial
        if not is_binomial(self.taxon):
           raise luigi.parameter.ParameterException('Taxon for BHL must be a binomial - taxon parameter is {}'.format(self.taxon))
        
    @abstractmethod
    def _get_ocr_text(self):
        return None  

    def run(self):
        data = []        
        detect_descriptions = BHLDetectDescriptions(self.taxon)
        ocr_text = self._get_ocr_text()
        logger.debug('Searching %s BHL pages for descriptions of %s', len(ocr_text), self.taxon)

        # Note: this is faster without using concurrent futures 
        for bhl_id, text in ocr_text.items():   
            
            if descriptions := detect_descriptions(text):
                logger.debug('%s descriptions detected in BHL page %s', len(descriptions), bhl_id)
                data.append({                        
                    'source': f"bhl",
                    'source_id': bhl_id,
                    'taxon': self.taxon,
                    'text': '\n\n'.join(descriptions) 
                })   

        logger.debug('BHLDescriptionTask: %s descriptions detected for taxon %s', len(data), self.taxon)
        with self.output().open('w') as f:            
            f.write(yaml.dump(data, explicit_start=True, default_flow_style=False)) 


class BHLDescriptionTask(BHLDescriptionBaseTask):
    
    """
    Aggregate search results from BHL
    """

    def requires(self):  
        return BHLSearchTask(taxon=self.taxon) 
            
    def _get_ocr_text(self):
        with self.input().open('r') as f:      
            return yaml.full_load(f)            
        
    def output(self):            
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.bhl.yaml')  
    

class BHLTesseractDescriptionTask(BHLDescriptionBaseTask):
    """
    Reparse descriptions using tesseract BHL
    """

    def requires(self):  
        # We have to do the dynamic dependencies this way, as if we put tasks
        # in run we get the error
        bhl_task = BHLDescriptionTask(taxon=self.taxon)
        luigi.build([bhl_task], local_scheduler=True)
        # We don;t have to yield this - but keeps the dependency graph accurate
        yield bhl_task
        with bhl_task.output().open() as f:
            bhl_descriptions = yaml.full_load(f)
            logger.debug('%s: Downloading %s pages for tesseract', self.taxon, len(bhl_descriptions))
            for bhl_description in bhl_descriptions:
                page_id = bhl_description['source_id']
                yield BHLTesseractOCRTask(page_id=page_id)
    
    def _get_ocr_text(self):
        data = {}
        for task_input in self.input():
            # Ignore the description task we used to build the requirements 
            if str(BHLTesseractOCRTask.output_dir) not in task_input.path: continue
            
            with task_input.open('r') as f:      
                page_id = Path(task_input.path).stem
                data[page_id] = f.read()

        logger.debug('%s: %s descriptions detected', self.taxon, len(data))

        return data


    def output(self):            
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.tesseract.yaml') 
    
if __name__ == "__main__":    
    import time
    start = time.time()   
    
    # p = INPUT_DATA_DIR / 'peatland-species.csv'
    
    # df = pd.read_csv(p)
    
    # taxa = df['Species name'].unique()
    
    # print(taxa[:2])
    
    # binomials = [taxon.strip() for taxon in taxa if len(taxon.split()) == 2]
    
    # binomials = ['Galium aparine']
    
    # binomials = binomials[:1]
    
    # print(binomials)
            
    # luigi.build([BHLAggregateOCRTask(bhl_ids=l, taxon='Metopium toxiferum')], local_scheduler=True) 
    # luigi.build([BHLDescriptionTask(taxon=taxon) for taxon in binomials], local_scheduler=True)
    luigi.build([BHLTesseractDescriptionTask(taxon='Achillea millefolium', force=True)], local_scheduler=True)
    # luigi.build([BHLDescriptionTask(bhl_id=27274329, force=True)], local_scheduler=True) 
    stop = time.time()
    print(stop-start)             
    
