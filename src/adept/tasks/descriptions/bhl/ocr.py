import luigi
import logging
import pandas as pd
import pytesseract
import yaml
import re

from adept.config import INTERMEDIATE_DATA_DIR
from adept.tasks.base import BaseTask
from adept.tasks.descriptions.bhl.image import BHLImageTask
from adept.bhl.preprocess import BHLPreprocess, BHLParagraphizer

class BHLOCRTask(BaseTask):
    
    bhl_id = luigi.IntParameter()
    
    preprocess= BHLPreprocess()
    
    def requires(self):
        return BHLImageTask(bhl_id=self.bhl_id)     
    
    def run(self):
        text = pytesseract.image_to_string(self.input().path)
        paragraphs = [self.preprocess(para) for para in BHLParagraphizer(text)]
    
        with self.output().open('w') as f:
            f.write(yaml.dump(paragraphs, explicit_start=True, default_flow_style=False)    ) 
            
    def output(self):
        return luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'bhl' / 'text' / f'{self.bhl_id}.yaml')             
            
            
if __name__ == "__main__":
    
    luigi.build([BHLOCRTask(bhl_id=27274329)], local_scheduler=True)