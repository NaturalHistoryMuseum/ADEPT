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
from pathlib import Path
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
from abc import ABCMeta, abstractmethod

from adept.config import INTERMEDIATE_DATA_DIR, logger, INPUT_DATA_DIR, Settings
from adept.tasks.base import BaseTask, BaseExternalTask
from adept.utils.request import CachedRequest
from adept.bhl.ocr_archive import BHLOCRArchive

class BHLTextTask(BaseExternalTask, metaclass=ABCMeta):

    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'text'

    @abstractmethod
    def get_text(self):
        pass

    def run(self):  
        text = self.get_text() or bytes()
        with self.output().open('wb') as f:
            f.write(text)

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.page_id}.txt', format=luigi.format.Nop)     

class BHLTextAPITask(BHLTextTask):
    page_id = luigi.IntParameter()  

    def get_text(self):
        url = f'https://www.biodiversitylibrary.org/pagetext/{self.page_id}'
        r = CachedRequest(url)   
        return r.text      

class BHLTextArchiveTask(BHLTextTask):

    if Settings.get('BHL_OCR_ARCHIVE_PATH'):
        _archive = BHLOCRArchive(Settings.get('BHL_OCR_ARCHIVE_PATH')) 

    page_id = luigi.IntParameter()     
    item_id = luigi.IntParameter()  
    seq_order = luigi.IntParameter()       

    def get_text(self):        
        text = self._archive.get_text(page_id=self.page_id, item_id=self.item_id, seq_order=self.seq_order)
        if not text:
            logger.critical(f'Page not found in archive: page_id:{self.page_id} item_id:{self.item_id} seq_order:{self.seq_order}')
        return text

if __name__ == "__main__":    
    import time
    start = time.time()
    luigi.build([BHLTextArchiveTask(page_id=38362363, item_id=118071, seq_order=311, force=True)], local_scheduler=True)
    stop = time.time()
    print(stop-start)    


    # 118071_38362363_311