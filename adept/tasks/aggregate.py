import luigi
import pandas as pd
import numpy as np
import re
from pandas.api.types import is_numeric_dtype
from pathlib import Path
import itertools
import yaml
from abc import ABC, abstractmethod,ABCMeta

from adept.config import TaxonomicGroup, logger, INTERMEDIATE_DATA_DIR, Settings
from adept.tasks.descriptions import DescriptionsTask
from adept.tasks.base import BaseTask
from adept.utils.helpers import list_uuid
from adept.utils.aggregator import Aggregator
from adept.tasks.description.ecoflora.description import EcofloraDescriptionTask
from adept.tasks.description.bhl.description import BHLDescriptionTask
from adept.tasks.description.efloras.description import EflorasChinaDescriptionTask, EflorasMossChinaDescriptionTask, EflorasNorthAmericaDescriptionTask, EflorasPakistanDescriptionTask
from adept.utils.helpers import is_binomial

              
 
                    
class AggregateTrainingDescriptionsTask(BaseTask):    
    """
    Aggregate descriptions. Used for generating descriptions for training data etc.,

    """
        
    taxa = luigi.ListParameter()
    output_dir = INTERMEDIATE_DATA_DIR / 'training-descriptions'

    def requires(self):
        for taxon in self.taxa:
            yield from [
                EcofloraDescriptionTask(taxon=taxon),
                EflorasNorthAmericaDescriptionTask(taxon=taxon),
                EflorasChinaDescriptionTask(taxon=taxon),
                EflorasMossChinaDescriptionTask(taxon=taxon),
                EflorasPakistanDescriptionTask(taxon=taxon),
                BHLDescriptionTask(taxon=taxon)
            ]    
        
    def run(self):
        data = []

        for task_input in self.input():
            with task_input.open('r') as f:
                descriptions = yaml.full_load(f)             
                data.extend([d for d in descriptions if d['description']])
        
        pd.DataFrame(data).to_csv(self.output().path, index=False)
    
    def output(self):
        file_name = f"{ Settings.get('BHL_OCR_SOURCE').name.lower()}.descriptions.csv"
        return luigi.LocalTarget(self.output_dir / file_name)        
    

if __name__ == "__main__":    
        
    taxa = [
        'Achillea millefolium',
    ]
    
    task = AggregateTrainingDescriptionsTask(taxa=taxa, taxonomic_group=TaxonomicGroup.angiosperm, force=True)    
    task.rebuild_descriptions()
    
    luigi.build([
        task
    ], local_scheduler=True) 
    
    print('Task complete: traits written to ', task.output().path)
