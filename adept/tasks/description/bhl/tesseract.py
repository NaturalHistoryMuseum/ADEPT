import luigi
import logging
import pandas as pd
import pytesseract
import yaml
import re
from pathlib import Path
import concurrent

from adept.config import INTERMEDIATE_DATA_DIR, logger
from adept.tasks.base import BaseTask
from adept.tasks.description.bhl.image import BHLImageTask

class BHLTesseractOCRTask(BaseTask):
    
    page_id = luigi.IntParameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'tesseract'
    
    def requires(self):
        return BHLImageTask(page_id=self.page_id)     
    
    def run(self):
        logger.info('Running BHL OCR Task for %s', self.page_id)        
        text = self.image_to_string(self.input().path)                 
        with self.output().open('w') as f:
            f.write(text)   
    
    @staticmethod            
    def image_to_string(image_path: Path):
        try:
            return pytesseract.image_to_string(image_path)
        except pytesseract.pytesseract.TesseractError as e:
            # Some files from BHL and empty - ignore
            logger.error('Error reading test from image %s: %s', image_path, e)

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.page_id}.txt')       
    
if __name__ == "__main__":    
    luigi.build([BHLTesseractOCRTask(page_id=63297052, force=True)], local_scheduler=True)