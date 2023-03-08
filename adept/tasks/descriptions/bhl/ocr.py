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
from adept.tasks.descriptions.bhl.images import BHLImagesTask

class BHLOCRTask(BaseTask):
    
    taxon = luigi.Parameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'ocr'
    
    def requires(self):
        return BHLImagesTask(taxon=self.taxon)     
    
    def run(self):
        logger.info('Running BHL OCR Task for %s', self.taxon)        
        data = {}                     
        image_dir = Path(self.input().path).parent                           
        with self.input().open('r') as f:
            images = yaml.full_load(f)                  
            # images = images[:5]        
        logger.info('OCRing %s images for %s', len(images), self.taxon)   
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            tasks = {executor.submit(self.image_to_string, p): p.stem for image in images if (p := image_dir / image) and p.is_file()}
            for future in concurrent.futures.as_completed(tasks):                
                page_id = tasks[future]
                data[page_id] = future.result()
                
        logger.info('Outputting %s OCR text for %s', len(data), self.taxon) 
        with self.output().open('w') as f:
            f.write(yaml.dump(data, explicit_start=True))   
    
    @staticmethod            
    def image_to_string(image_path: Path):
        try:
            return pytesseract.image_to_string(str(image_path))
        except pytesseract.pytesseract.TesseractError as e:
            # Some files from BHL and empty - ignore
            logger.error('Error reading test from image %s: %s', image_path, e)

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.yaml')       
    
if __name__ == "__main__":    
    luigi.build([BHLOCRTask(taxon='Leersia hexandra', force=True)], local_scheduler=True)