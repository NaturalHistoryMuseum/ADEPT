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

class BHLImagesTask(BaseTask):
    """
    Loop through results from search, downloading the images

    Output: index file of images 

    Args:
        luigi.Parameter: taxon
    """
    
    taxon = luigi.Parameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'images'   
    max_image_dimension = 2000
    
    def requires(self):        
       return BHLSearchTask(taxon=self.taxon)   
   
    def run(self):        
 
        output_path = Path(self.output().path)              
        image_dir = output_path.parent
        image_dir.mkdir(parents=True, exist_ok=True)  
        with self.input().open('r') as f: 
            search_results = yaml.full_load(f)                
        page_ids = search_results.keys()                
        logger.info('BHL Images: %s images found for %s', len(page_ids), self.taxon)          
        self.download_images(page_ids, image_dir)
        images = [p.name for page_id in page_ids if (p := self._image_path(image_dir, page_id)) and p.is_file()]
        
        # Output to text file, one pat per line, suitable for tesseract bath processing
        with self.output().open('w') as f:
            f.write(yaml.dump(images, explicit_start=True, default_flow_style=False)) 
        
    def output(self):
        return luigi.LocalTarget(self.output_dir / self.taxon / 'index.yaml')       
            
    @staticmethod
    def _image_path(image_dir, page_id):              
        return  image_dir / f'{page_id}.tif'
            
    def download_images(self, page_ids, image_dir):

        with FuturesSession(max_workers=20) as session:
            def _future(page_id):
                future = session.get(f'https://www.biodiversitylibrary.org/pageimage/{page_id}')
                future.page_id = page_id
                return future

            futures=[_future(page_id) for page_id in page_ids if not self._image_path(image_dir, page_id).is_file()]    
            
            for future in as_completed(futures):
                r = future.result()
                if not len(r.content):
                    continue
                    
                img = Image.open(BytesIO(r.content))
                
                # print(f'W: {img.width} H: {img.height}')
                
                img = self.resize_image(img)
                img.save(self._image_path(image_dir, future.page_id),  "TIFF", quality=100, subsampling=0)
            
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
    luigi.build([BHLImagesTask(taxon='Leersia hexandra', force=True)], local_scheduler=True)
    stop = time.time()
    print(stop-start)      