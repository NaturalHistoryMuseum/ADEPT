
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

from adept.config import INTERMEDIATE_DATA_DIR, logger, INPUT_DATA_DIR, Settings, BHL_NAMES_INDEX_PATH, BHL_OCR_ARCHIVE_PATH
from adept.tasks.base import BaseTask, BaseExternalTask
from adept.utils.request import CachedRequest
from adept.tasks.description.bhl.text import BHLTextTask
from adept.traits import SimpleTraitTextClassifier
from adept.tasks.description.bhl import BHL_BASE_URL
from adept.traits import SimpleTraitTextClassifier
from adept.worldflora import WorldFlora


class BHLSearchTask(BaseTask):
    
    """
    Search BHL for a taxon            
    """

    taxon = luigi.Parameter()    
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'search'
    try:
        names = pd.read_parquet(BHL_NAMES_INDEX_PATH) 
    except FileNotFoundError:
        raise RuntimeError(
            f"{BHL_NAMES_INDEX_PATH} missing.\n"
            "Run: `adept assets bhl-names` to download required data."
        )        

    # Can change min_terms - lower = slower; higher = less images download but might miss some
    trait_classifier = SimpleTraitTextClassifier(min_terms=15, min_chars=2500)
    wf = WorldFlora()

    def requires(self):
        for row in self.search().itertuples():

            yield BHLTextTask(
                page_id=row.PageID,
                item_id=row.ItemID,
                seq_order=row.SequenceOrder,               
            )
 
    def search(self): 
        if synonyms := self.wf.get_related_names(self.taxon):
            logger.debug(f'{len(synonyms)} Synonyms found for {self.taxon}')
            synonyms.add(self.taxon)
            return self.names[self.names.NameConfirmed.isin(synonyms)]
        else:
            return self.names[self.names.NameConfirmed == self.taxon]
                           
    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.en.yaml')              
            
    def run(self): 
        data = {}
        for i in self.input():
            p = Path(i.path)
            page_id = int(p.stem)
            with p.open() as f:
                text = f.read()
                if text and self._is_description(text):
                    data[page_id] = text
 
        with self.output().open('w') as f:                  
            f.write(yaml.dump(data, explicit_start=True, default_flow_style=False))             
                           
    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.taxon}.en.yaml') 

    def _is_description(self, text):
        """
        So many results in BHL (some taxa, 1000s of pages), and mostly are irrelevant. 
        If we download and then OCR the image and then check for a description, this
        pipeline takes ages. 
        
        So use the BHL OCRd text with the simple text classier
        to determine if the page is worth including in the search results        
        """
        return self.trait_classifier.is_description(text) 
    
if __name__ == "__main__":    
    import time
    start = time.time()
    luigi.build([BHLSearchTask(taxon='Leersia hexandra', force=True)], local_scheduler=True)

    # x = BHLTaxonSearchTask(taxon='Leersia hexandra')
    # print(x.search())

    stop = time.time()
    print(stop-start)          