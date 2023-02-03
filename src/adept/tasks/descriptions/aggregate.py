import luigi
import pandas as pd
from pathlib import Path
import yaml

from adept.config import taxonomic_groups, logger, PROCESSED_DATA_DIR, DATA_DIR, INTERMEDIATE_DATA_DIR
from adept.tasks.base import BaseTask
from adept.tasks.descriptions.ecoflora.description import EcofloraDescriptionTask
from adept.tasks.descriptions.bhl.description import BHLDescriptionTask
from adept.tasks.descriptions.efloras.description import EflorasChinaDescriptionTask, EflorasMossChinaDescriptionTask, EflorasNorthAmericaDescriptionTask, EflorasPakistanDescriptionTask
from adept.utils.helpers import list_uuid


class AggregateDescriptionsTask(BaseTask):    
    """
    Aggregate descriptions 

    """
        
    taxon_names = luigi.ListParameter()

    def requires(self):
        for taxon in self.taxon_names:
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
                print(descriptions)
                data.extend([d for d in descriptions if d['description']])
        
        pd.DataFrame(data).to_csv(self.output().path, index=False)
    
    def output(self):
        uuid = list_uuid(self.taxon_names)
        return luigi.LocalTarget(PROCESSED_DATA_DIR / f'{uuid}.descriptions.csv') 
    
if __name__ == "__main__":    
    
    
    
    # luigi.build([AggregateTask(taxon_names=["Acer caudatum"], taxonomic_group='angiosperm', force=True)], local_scheduler=True)    
    
    file_path = DATA_DIR / 'input/north-american-assessments.csv'
    # luigi.build([AggregateFileTask(taxonomic_group='angiosperm', force=True, file_path=file_path)], local_scheduler=True)
    
    
    taxa = [        

        "Metopium toxiferum",
        "Ancistrocladus guineensis"          
    ]
    
    luigi.build([AggregateDescriptionsTask(taxon_names=taxa, force=True)], local_scheduler=True)