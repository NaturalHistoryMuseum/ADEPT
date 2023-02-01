
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

from adept.config import INTERMEDIATE_DATA_DIR, logger, BHL_API_KEY
from adept.utils.soup import RequestSoup
from adept.utils.enum import Enum
from adept.traits import SimpleTraitTextClassifier
from adept.tasks.descriptions.description import DescriptionTask

from adept.tasks.descriptions.bhl.search import BHLSearchTask
from adept.tasks.descriptions.bhl.ocr import OCRTask
from adept.tasks.base import BaseTask
from adept.utils.request import CachedRequest

def something():
    print("XXX")
    print("SOMETHING")
    print("XXX")
    return



class BHLDescriptionTask(BaseTask):
    
    bhl_id = luigi.IntParameter()
    # taxonerd = TaxoNERD(prefer_gpu=False)
    # nlp = taxonerd.load(model="en_core_eco_biobert")
    some = something()
    
    def requires(self):        
       return OCRTask(bhl_id=self.bhl_id)    

    def run(self):        
        description = self.get_taxon_description()        
        with self.output().open('w') as f:
            f.write(description or '')

    def get_taxon_description(self): 
        
        with self.input().open('r') as f:
            paragraphs =  yaml.safe_load(f)
            
               
        return 'HELLO'

        
    def output(self):
        return luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'bhl' / 'text' / f'{self.bhl_id}2.txt')      

class BHLDescriptionsTask(BaseTask):
    
    """
    Search BHL for a taxon            
    """

    taxon = luigi.Parameter()
    
    def requires(self):        
       return BHLSearchTask(taxon=self.taxon)
        # return BHLDescriptionTask(bhl_id=27274329)
            
    def run(self):
        
        
        # for page_id in self.page_ids():
        #     print(page_id)
        # yield [BHLDescriptionTask(bhl_id=27274329)]
        
        # yield self.clone(BHLDescriptionTask, bhl_id=27274329)
        yield BHLDescriptionTask(bhl_id=27274329)
                      
            
    def page_ids(self):
        # with self.input().open('r') as f: 
        #     df = pd.read_csv(f)
        #     yield from df['page_id']
        
        return [27274329]
                                    
    def output(self):
        # Not all pf them are descriptions!!!  But do we still want the blank file?? I think so
        for page_id in self.page_ids():
            print(page_id)
            # yield luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'bhl' / 'description' / f'{self.taxon}.{page_id}.txt')              



   
   
    
if __name__ == "__main__":    
    
    # luigi.build([BHLDescriptionsTask(taxon='Metopium toxiferum')], local_scheduler=True) 
    luigi.build([BHLDescriptionTask(bhl_id=27274329, force=True)], local_scheduler=True)
    luigi.build([BHLDescriptionTask(bhl_id=37190518, force=True)], local_scheduler=True)
    # luigi.build([BHLDescriptionTask(bhl_id=27274329, force=True)], local_scheduler=True)      
    
    
#     uineensis,['A. guineensis'],18704181
# "Smooth climbing shrubs with short supra-axillary, often arrested and circinately-hooked, branches. Jieaves usually in terminal tufts, coriaceous, entire, reticulately feather-veined; exstipulate. Flowers usually small, very caducous, in terminal or lateral panicles. Calyxtube at first short, adnate to the base of the ovary, its lobes imbricate, finally turbinate and adnate to the fruit, with the lobes unequally enlarged, spreading and membranous. Stamens 5 or 10, subperigynous. Ovary 1-celled, inferior; style sub-globose, persistent; Stigmas 3, erect, compressed, truncate, deciduous. Ovule solitary, erect or laterally affixed. Seed sub-globose, testa prolonged into the ruminations of the copious fleshy albumen; embryo short, straight; cotyledons short, divergent.—Disrris. Except A. guineensis in W. Tropical Africa, confined to Tropical Asia and the Indian Archipelago, Species about 10.",Ancistrocladus guineensis,['A. guineensis'],37190518
# "Smooth climbing shrubs with short supra-axillary, often arrested and circinately-hooked, branches. Leaves usually in terminal tufts, coriaceous, entire, reticulately feather-veined; exstipulate. Flowers usually small, very caducous, in terminal or lateral panicles. Calyetube at first short, adnate to the base of the ovary, its lobes imbricate, finally turbinate and adnate to the fruit, with the lobes unequally enlarged, spreading and membranous. Stamens 5 or 10, subperigynous. Ovary 1-celled, inferior; style sub-globose, persistent; Stigmas 3, erect, compressed, truncate, deciduous. Ovule solitary, erect or laterally affixed. Seed sub-globose, testa prolonged into the ruminations of the copious fleshy albumen; embryo short, straight; cotyledons short, divergent.—Disrriz. Except A. guineensis in W. Tropical Africa, confined to Tropical Asia and the Indian Archipelago, Species about 10.",Ancistrocladus guineensis,['A. guineensis'],47292874