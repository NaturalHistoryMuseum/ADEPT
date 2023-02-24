import luigi
import urllib
from urllib.request import urlretrieve
import numpy as np
from PIL import Image

from adept.tasks.base import BaseExternalTask
from adept.tasks.descriptions.bhl import BHL_BASE_URL
from adept.config import INTERMEDIATE_DATA_DIR, logger

    
class BHLImageTask(BaseExternalTask):
    
    bhl_id = luigi.IntParameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'bhl' / 'image'
    
    def run(self):
        image_url = f'{BHL_BASE_URL}/pageimage/{self.bhl_id}'
        logger.debug('Retrieving image: %s', image_url)
        try:
            urlretrieve(image_url, self.output().path)
        except urllib.error.HTTPError as e:
            # Some images are on BHL - but not downloadable / 404
            logger.error('Error downloading image %s: %s', image_url, e)
            # We do not want downstream tasks to fail, so create fake image
            self._write_synthetic_image()

    def output(self):
        return luigi.LocalTarget(self.output_dir / f'{self.bhl_id}.jpg')  
    
    def _write_synthetic_image(self): 
        c = np.zeros((1,1))
        image = Image.fromarray(c.astype(np.uint8))
        image.save(self.output().path)        

if __name__ == "__main__":    
    luigi.build([BHLImageTask(bhl_id=8436104, force=True)], local_scheduler=True)
    
    