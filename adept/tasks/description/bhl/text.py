
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

from adept.config import INTERMEDIATE_DATA_DIR, logger, BHL_API_KEY, INPUT_DATA_DIR, BHL_OCR_ARCHIVE_PATH
from adept.tasks.base import BaseTask, BaseExternalTask
from adept.utils.request import CachedRequest
from adept.bhl.ocr_archive import BHLOCRArchive

class BHLTextTask(BaseExternalTask, metaclass=ABCMeta):

    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'text'

    @abstractmethod
    def get_text(self):
        pass

    def run(self):  
        if text := self.get_text():
            with self.output().open('w') as f:
                f.write(str(text))

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.page_id}.txt')     

class BHLTextAPITask(BHLTextTask):
    page_id = luigi.IntParameter()  

    def get_text(self):
        url = f'https://www.biodiversitylibrary.org/pagetext/{self.page_id}'
        r = CachedRequest(url)   
        return r.text      

class BHLTextArchiveTask(BHLTextTask):

    if BHL_OCR_ARCHIVE_PATH:
        _archive = BHLOCRArchive(BHL_OCR_ARCHIVE_PATH) 

    page_id = luigi.IntParameter()     
    item_id = luigi.IntParameter()  
    seq_order = luigi.IntParameter()       

    def get_text(self):        
        return self._archive.get_text(page_id=self.page_id, item_id=self.item_id, seq_order=self.seq_order)

