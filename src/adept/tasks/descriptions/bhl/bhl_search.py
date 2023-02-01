from traitlets import default
import luigi
import logging
import pandas as pd

from descriptor.bhl.search import BHLSearch
from descriptor.config import BHL_CACHE_DIR, logger
from descriptor.tasks.base import BaseTask

class BHLSearchTask(BaseTask):
    
    name = luigi.Parameter()
    
    # https://www.digitalocean.com/community/tutorials/how-to-build-a-data-processing-pipeline-using-luigi-in-python-on-ubuntu-20-04

    def output(self):
        return luigi.LocalTarget(BHL_CACHE_DIR / f'{self.name}.search.txt')

    def run(self):
        bhl = BHLSearch()
        name_list = bhl.name_list(self.name)
        df = pd.DataFrame(name_list) 

        logger.info(df.shape)

        df.to_csv(self.output().path, index=False)


if __name__ == "__main__":

    luigi.build([BHLSearchTask(name="Ancistrocladus guineensis", force=True)], local_scheduler=True)