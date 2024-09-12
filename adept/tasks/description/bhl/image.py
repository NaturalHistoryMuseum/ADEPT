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
from adept.utils.request import CachedRequest

class BHLImageTask(BaseTask):
    """
    Download the page image

    Output: image file

    Args:
        luigi.Parameter: page_id
    """
    
    page_id = luigi.IntParameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'images'   
    max_image_dimension = 2000  

    def run(self):  
        url = f'https://www.biodiversitylibrary.org/pageimage/{self.page_id}'
        r = CachedRequest(url)
        img = Image.open(BytesIO(r.content))
        resized_img = self.resize_image(img)
        resized_img.save(self.output().path,  "TIFF", quality=100, subsampling=0)

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.page_id}.tiff')       
            
    def resize_image(self, img):
        """
        If image has a dimension longer than max_image_dimension, resize the image
        """
        xy = np.array([img.width, img.height])            
        if xy.max() > self.max_image_dimension:
            r = self.max_image_dimension / xy.max()
            resized_xy = r * xy
            img = img.resize(resized_xy.astype(int))
        return img
                                
if __name__ == "__main__":    
    import time
    start = time.time()
    luigi.build([BHLImageTask(page_id=11321112)], local_scheduler=True)
    stop = time.time()
    print(stop-start)      