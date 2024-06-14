import luigi
import logging
import pandas as pd
import pytesseract
import yaml
import re
import numpy as np
from pathlib import Path
from io import BytesIO
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
from PIL import Image

from adept.config import INTERMEDIATE_DATA_DIR, logger
from adept.tasks.base import BaseTask
from adept.tasks.description.bhl.search import BHLSearchTask
from adept.utils.request import CachedRequest

class BHLPageTextTask(BaseTask):
    """
    Download the OCR'd page text

    Output: .txt file

    Args:
        luigi.Parameter: page_id
    """
    
    page_id = luigi.IntParameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'text'   

    def run(self):  
        url = f'https://www.biodiversitylibrary.org/pagetext/{self.page_id}.txt'
        r = CachedRequest(url)

        with self.output().open('w') as f:
            f.write(r.text)

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.page_id}.txt')       
            

class BHLPageImageTask(BaseTask):            
    pass
                            
if __name__ == "__main__":    
    import time
    start = time.time()
    luigi.build([BHLPageTextTask(page_id=63297052)], local_scheduler=True)
    stop = time.time()
    print(stop-start)      