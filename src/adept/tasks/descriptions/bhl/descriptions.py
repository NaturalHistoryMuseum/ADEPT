import luigi
import logging
import pandas as pd
from langdetect import detect 
import numpy as np

from descriptor.bhl.search import BHLSearch
from descriptor.config import BHL_CACHE_DIR
from descriptor.tasks.bhl_text import BHLTextTask
from descriptor.tasks.ocr import OCRTask
from descriptor.tasks.base import BaseTask
from descriptor.paragraphizer import Paragraphizer
from descriptor.traits import Traits
from descriptor.preprocessor import Preprocessor
from taxonerd import TaxoNERD


class DescriptionsTask(BaseTask):
    
    name = luigi.Parameter()
    traits = Traits()
    preprocessor = Preprocessor()
    taxonerd = TaxoNERD(prefer_gpu=False)
    nlp = taxonerd.load(model="en_core_eco_biobert")
    
    def requires(self):
        return BHLTextTask(name=self.name) 
    
    def run(self):
        
        print(self.input().path)

        df = pd.read_csv(self.input().path)
        for page in df.itertuples():
            
            # Basic match to detect traits on the page - skips index pages etc.,
            trait_matches = self.traits.trait_terms_in_text(page.text)
            if len(trait_matches['terms']) < 10:
                continue
            
            paragraphs = Paragraphizer(page.text)
            for paragraph in paragraphs:
                
                text = self.preprocessor(paragraph)
                
                # print(text)
                print('----')
                
            break

            
    def output(self):
        return luigi.LocalTarget(BHL_CACHE_DIR / f'{self.name}.descriptions.csv')
        
    
        
        
if __name__ == "__main__":
    
    luigi.build([DescriptionsTask(name="Ancistrocladus guineensis", force=True)], local_scheduler=True)        