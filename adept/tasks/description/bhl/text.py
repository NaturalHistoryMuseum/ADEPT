import luigi
import os
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
from pathlib import Path
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
from abc import ABCMeta, abstractmethod

from adept.config import INTERMEDIATE_DATA_DIR, logger, INPUT_DATA_DIR, Settings, BHL_OCR_ARCHIVE_PATH, BHL_OCR_ARCHIVE_PATH_ALLOW_EMPTY
from adept.tasks.base import BaseTask, BaseExternalTask
from adept.bhl.ocr import BHLOCR

class BHLTextTask(BaseExternalTask, metaclass=ABCMeta):

    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'text'
    page_id = luigi.IntParameter()     
    item_id = luigi.IntParameter()  
    seq_order = luigi.IntParameter()      

    def archive_get_text(self):  
        # Pad with the required number of zeros
        page_id = str(self.page_id).zfill(8)
        item_id = str(self.item_id).zfill(6)
        seq_order = str(self.seq_order).zfill(4)       

        if not BHL_OCR_ARCHIVE_PATH_ALLOW_EMPTY:
            with os.scandir(BHL_OCR_ARCHIVE_PATH) as entries:
                if next(entries, None) is None:            
                    raise Exception('BHL OCR Archive is empty - please run adept assets bhl-ocr')
         
        p = BHL_OCR_ARCHIVE_PATH / f"{item_id}-{page_id}-{seq_order}.txt"    
          
        with p.open('r') as f:
            text = f.read()       
        return text.encode("utf-8")

    def api_get_text(self):
        ocr = BHLOCR()

        text = ocr.get_page_ocr(self.page_id)

        if text is None:
            raise FileNotFoundError(
                f"No OCR text found for BHL page {self.page_id}"
            )

        return text.encode("utf-8")     

    def run(self):  
        try:
            text = self.archive_get_text()
        except FileNotFoundError:
            logger.info(f'Page {self.page_id} not found in archive - retrieving text with API')
            text = self.api_get_text()

        if text:
            with self.output().open('wb') as f:
                f.write(text)

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.page_id}.txt', format=luigi.format.Nop)     

if __name__ == "__main__":    
    import time
    start = time.time()

    # 099150-31766113-0066

    # luigi.build([BHLTextTask(page_id=38362363, item_id=118071, seq_order=311, force=True)], local_scheduler=True)
    # luigi.build([BHLTextTask(page_id='31766113', item_id='099150', seq_order='66', force=True)], local_scheduler=True)

    # BHLTextTask(page_id=5434779, item_id=27995, seq_order=55)



    luigi.build([BHLTextTask(page_id='15469214', item_id='52984', seq_order='414', force=True)], local_scheduler=True)
    stop = time.time()
    print(stop-start)    


    # 118071_38362363_311