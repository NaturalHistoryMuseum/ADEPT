import luigi
import logging
import pandas as pd
from langdetect import detect 
import numpy as np

from descriptor.bhl.search import BHLSearch
from descriptor.config import BHL_CACHE_DIR
from descriptor.tasks.bhl_search import BHLSearchTask
from descriptor.tasks.ocr import OCRTask
from descriptor.tasks.base import BaseTask

class BHLTextTask(BaseTask):
    
    name = luigi.Parameter()
    
    def requires(self):
        return BHLSearchTask(name=self.name) 
    
    def run(self):
        
        output = []
        
        # https://www.markhneedham.com/blog/2017/03/28/luigi-defining-dynamic-requirements-on-output-files/
        ocr_tasks = []
        df = pd.read_csv(self.input().path)
        
        # Move this to search.
        
        df['page_id'] = df['Url'].apply(lambda url: url.split('/')[-1])
        # Detect english language title - BHL Language isn't always set correctly
        df['detected_lang'] = df.Title.apply(self._detect_language)
        # Filter out not endlish languages
        df = df[(df['detected_lang'] == 'en') | (df.Language == 'English')]

        # Descriptions requires OCR task
        # Which requires search tasl
        # Which requires name list

        for page_id in df['page_id']:
            ocr_task = OCRTask(bhl_id=page_id)
            ocr_tasks.append(ocr_task)
            # Need to yield task so it's added to the scheduler and called
            yield ocr_task
            
        for ocr_task in ocr_tasks:
            with ocr_task.output().open('r') as f:
                output.append({
                    'name': self.name,
                    'text': f.read(),
                    'bhl_id': ocr_task.bhl_id
                })

        df = pd.DataFrame(output)
        df.to_csv(self.output().path, index=False)

            
    def output(self):
        return luigi.LocalTarget(BHL_CACHE_DIR / f'{self.name}.text.csv')
       
    @staticmethod 
    def _detect_language(title):
        try:
            return detect(title)
        except:
            return np.nan     
        
        
if __name__ == "__main__":
    
    luigi.build([BHLTextTask(name="Ancistrocladus guineensis", force=True)], local_scheduler=True)        