
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
from langdetect import detect 
import numpy as np
from urllib.request import urlretrieve
from requests.models import PreparedRequest
from taxonerd import TaxoNERD
from pathlib import Path

from adept.config import INTERMEDIATE_DATA_DIR, logger, BHL_API_KEY
from adept.utils.soup import RequestSoup
from adept.utils.enum import Enum
from adept.traits import SimpleTraitTextClassifier


from adept.bhl.postprocess import BHLPostprocess

from adept.tasks.descriptions.bhl.search import BHLSearchTask
from adept.tasks.descriptions.bhl.ocr import BHLAggregateOCRTask
from adept.tasks.base import BaseTask
from adept.utils.helpers import is_binomial

class BHLDescriptionTask(BaseTask):
    
    """
    Search BHL for a taxon            
    """

    taxon = luigi.Parameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'description'
    postprocess = BHLPostprocess()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        # Taxon for BHL must be a binomial
        if not is_binomial(self.taxon):
           raise luigi.parameter.ParameterException('Taxon for BHL must be a binomial - taxon parameter is {}'.format(self.taxon))
    
    def requires(self):        
       return BHLSearchTask(taxon=self.taxon)
            
    def run(self):
        
        data = []
        
        with self.input().open('r') as f: 
            df = pd.read_csv(f)
            bhl_ids = df['page_id'].unique().tolist()
            agg_task_target = yield BHLAggregateOCRTask(bhl_ids=bhl_ids, taxon=self.taxon)
            
        with agg_task_target.open('r') as f:
            bhl_pages =  yaml.safe_load(f)
            for page in bhl_pages:
                if not page.get('text'): continue                
                if descriptions := list(self.postprocess(self.taxon, page['text'])):
                    data.append({
                        'bhl_id': page['bhl_id'],
                        'source': f"bhl.{page['bhl_id']}",
                        'taxon': self.taxon,
                        'text': '\n\n'.join(descriptions) 
                    })            
                  
        with self.output().open('w') as f:
            f.write(yaml.dump(data, explicit_start=True, default_flow_style=False)) 
                        
    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.yaml')  



    
if __name__ == "__main__":    
       
    # luigi.build([BHLAggregateOCRTask(bhl_ids=l, taxon='Metopium toxiferum')], local_scheduler=True) 
    # luigi.build([BHLDescriptionTask(taxon='Metopium toxiferum')], local_scheduler=True)
    luigi.build([BHLDescriptionTask(taxon='Eleocharis', force=True)], local_scheduler=True)
    # luigi.build([BHLDescriptionTask(bhl_id=27274329, force=True)], local_scheduler=True)      
    
    
#     uineensis,['A. guineensis'],18704181
# "Smooth climbing shrubs with short supra-axillary, often arrested and circinately-hooked, branches. Jieaves usually in terminal tufts, coriaceous, entire, reticulately feather-veined; exstipulate. Flowers usually small, very caducous, in terminal or lateral panicles. Calyxtube at first short, adnate to the base of the ovary, its lobes imbricate, finally turbinate and adnate to the fruit, with the lobes unequally enlarged, spreading and membranous. Stamens 5 or 10, subperigynous. Ovary 1-celled, inferior; style sub-globose, persistent; Stigmas 3, erect, compressed, truncate, deciduous. Ovule solitary, erect or laterally affixed. Seed sub-globose, testa prolonged into the ruminations of the copious fleshy albumen; embryo short, straight; cotyledons short, divergent.—Disrris. Except A. guineensis in W. Tropical Africa, confined to Tropical Asia and the Indian Archipelago, Species about 10.",Ancistrocladus guineensis,['A. guineensis'],37190518
# "Smooth climbing shrubs with short supra-axillary, often arrested and circinately-hooked, branches. Leaves usually in terminal tufts, coriaceous, entire, reticulately feather-veined; exstipulate. Flowers usually small, very caducous, in terminal or lateral panicles. Calyetube at first short, adnate to the base of the ovary, its lobes imbricate, finally turbinate and adnate to the fruit, with the lobes unequally enlarged, spreading and membranous. Stamens 5 or 10, subperigynous. Ovary 1-celled, inferior; style sub-globose, persistent; Stigmas 3, erect, compressed, truncate, deciduous. Ovule solitary, erect or laterally affixed. Seed sub-globose, testa prolonged into the ruminations of the copious fleshy albumen; embryo short, straight; cotyledons short, divergent.—Disrriz. Except A. guineensis in W. Tropical Africa, confined to Tropical Asia and the Indian Archipelago, Species about 10.",Ancistrocladus guineensis,['A. guineensis'],47292874