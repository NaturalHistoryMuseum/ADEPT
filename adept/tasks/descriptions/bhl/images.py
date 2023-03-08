import luigi
import logging
import pandas as pd
import pytesseract
import yaml
import re
from pathlib import Path
from io import BytesIO
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
from PIL import Image

from adept.config import INTERMEDIATE_DATA_DIR, logger
from adept.tasks.base import BaseTask
from adept.tasks.descriptions.bhl.search import BHLSearchTask

class BHLImagesTask(BaseTask):
    """
    Loop through results from search, downloading the images

    Output: index file of images 

    Args:
        luigi.Parameter: taxon
    """
    
    taxon = luigi.Parameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'images'   
    image_width = 1800
    
    def requires(self):        
       return BHLSearchTask(taxon=self.taxon)   
   
    def run(self):        
 
        output_path = Path(self.output().path)              
        image_dir = output_path.parent
        image_dir.mkdir(parents=True, exist_ok=True)  
        with self.input().open('r') as f: 
            search_results = yaml.full_load(f)        
            
        logger.info('BHL Images: %s images found for %s', len(search_results), self.taxon)          
        self.download_images(search_results, image_dir)
        images = [p.name for page_id in search_results if (p := self._image_path(image_dir, page_id)) and p.is_file()]
        
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
                r = self.image_width / img.width
                image_height = round(img.height * r)
                # img = img.resize((self.image_width, image_height))
                img.save(self._image_path(image_dir, future.page_id),  "TIFF", quality=100, subsampling=0)
            
            
if __name__ == "__main__":    
    import time
    start = time.time()
    luigi.build([BHLImagesTask(taxon='Leersia hexandra', force=True)], local_scheduler=True)
    stop = time.time()
    print(stop-start)      