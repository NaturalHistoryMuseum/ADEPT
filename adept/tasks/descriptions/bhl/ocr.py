from asyncio.log import logger
import luigi
import logging
import pandas as pd
import pytesseract
import yaml
import re
from pathlib import Path

from adept.config import INTERMEDIATE_DATA_DIR
from adept.tasks.base import BaseTask
from adept.tasks.descriptions.bhl.image import BHLImageTask
from adept.bhl.preprocess import BHLPreprocess, BHLParagraphizer

class BHLOCRTask(BaseTask):
    
    bhl_id = luigi.IntParameter()
    
    preprocess= BHLPreprocess()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'ocr-text'
    
    def requires(self):
        return BHLImageTask(bhl_id=self.bhl_id)     
    
    def run(self):
        with self.output().open('w') as f:
            try:
                text = pytesseract.image_to_string(self.input().path)
            except pytesseract.pytesseract.TesseractError as e:
                # Some files from BHL and empty - ignore
                logger.error('Error reading test from image %s: %s', self.input().path, e)
            else:
                paragraphs = [self.preprocess(para) for para in BHLParagraphizer(text)]
                f.write(yaml.dump(paragraphs, explicit_start=True, default_flow_style=False)) 
            
    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.bhl_id}.yaml')       
    
    
class BHLAggregateOCRTask(BaseTask):
    
    """
    
    Aggrgates multiple OCR outputs into one single file

    """
    
    bhl_ids = luigi.ListParameter()
    taxon = luigi.Parameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'aggregated-ocr-text'
    
    def requires(self):        
        for bhl_id in self.bhl_ids:
            yield BHLOCRTask(bhl_id=bhl_id)
                        
    def run(self):
        data = [] 

        for ocr_input in self.input():
            bhl_id = Path(ocr_input.path).stem
            with ocr_input.open('r') as f:
                ocr_text =  yaml.safe_load(f)
                data.append({
                    'bhl_id': bhl_id,
                    'text': ocr_text
                })
                
        with self.output().open('w') as f:
            f.write(yaml.dump(data, explicit_start=True))                    

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.yaml')          
            
            
if __name__ == "__main__":
    
    luigi.build([BHLOCRTask(bhl_id=8436104)], local_scheduler=True)