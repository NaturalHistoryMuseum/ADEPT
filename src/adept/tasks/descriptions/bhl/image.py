import luigi
from urllib.request import urlretrieve

from adept.tasks.descriptions.bhl import BHL_BASE_URL
from adept.config import INTERMEDIATE_DATA_DIR, logger

    
class BHLImageTask(luigi.ExternalTask):
    
    bhl_id = luigi.IntParameter()
    
    def run(self):
        image_url = f'{BHL_BASE_URL}/pageimage/{self.bhl_id}'
        logger.debug('Retrieveing image: ', image_url)
        urlretrieve(image_url, self.output().path)

    def output(self):
        return luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'bhl' / 'image' / f'{self.bhl_id}.jpg')   

    
    