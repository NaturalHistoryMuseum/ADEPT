import luigi
import pandas as pd
import numpy as np
import re
from pandas.api.types import is_numeric_dtype
from pathlib import Path
import itertools
import yaml
from abc import ABC, abstractmethod,ABCMeta

from adept.config import TaxonomicGroup, logger, OUTPUT_DATA_DIR, OCR_MODEL
from adept.tasks.descriptions import DescriptionsTask
from adept.tasks.base import BaseTask
from adept.utils.helpers import list_uuid
from adept.utils.aggregator import Aggregator
from adept.tasks.description.ecoflora.description import EcofloraDescriptionTask
from adept.tasks.description.bhl.description import BHLDescriptionTask
from adept.tasks.description.efloras.description import EflorasChinaDescriptionTask, EflorasMossChinaDescriptionTask, EflorasNorthAmericaDescriptionTask, EflorasPakistanDescriptionTask
  

class AggregateBaseTask(BaseTask):  
    
    @property
    def uuid(self):
        if len(self.taxa) == 1:
            return self.taxa[0].lower().replace(' ', '-')
        else:
            return list_uuid(self.taxa)
              
class AggregateTraitsTask(AggregateBaseTask):              
                     
    taxa = luigi.ListParameter()
    taxonomic_group = luigi.EnumParameter(enum=TaxonomicGroup) 
    aggregator = Aggregator()   
    
    def requires(self):
        for taxon in self.taxa:
            yield DescriptionsTask(taxon=taxon, taxonomic_group=self.taxonomic_group)      

    def run(self):
        
        dfs = []    
        combined_dfs = []

        for input_json in self.input():     
            df = pd.read_json(input_json.path)            
            if not df.empty:              
                df.taxon = df.taxon.str.capitalize()  
                column_mappings = self.aggregator.get_column_mappings(df, exclude=['taxon'])                                
                combined = df.groupby('taxon').agg(column_mappings)                   
                dfs.append(df)
                combined_dfs.append(combined)            
        
        if not combined_dfs:        
            # If we have no descriptions at all - if searching for single taxa 
            logger.critical('No descriptions located')
            return
            
        combined_dfs = pd.concat(combined_dfs)
        
        combined_dfs = combined_dfs.drop(columns=['source', 'source_id'])
        dfs = pd.concat(dfs)
        cols = set(dfs.columns).difference(set(['taxon', 'source', 'source_id']))
        combined_dfs = combined_dfs.dropna(subset=cols, how="all")
        ordered_combined_cols = [c for c in dfs.columns.tolist() if c in combined_dfs.columns.tolist()]
        
        with pd.ExcelWriter(self.output().path) as writer:    
            combined_dfs.to_excel(writer, sheet_name="combined", columns=ordered_combined_cols)
            for source, group in dfs.groupby('source'):
                # If we don't have any values in a row, drop it         
                group = group.dropna(subset=cols, how="all")               
                if not group['source_id'].any(): group.drop('source_id', axis=1, inplace=True)
                # Ensure taxon is first column 
                ordered_cols = list(dict.fromkeys(['taxon'] + group.columns.tolist()))               
                group.to_excel(writer, sheet_name=source, index=False, columns=ordered_cols)                              
        
    def output(self):
        output_dir = OUTPUT_DATA_DIR / OCR_MODEL.name.lower()
        output_dir.mkdir(parents=True, exist_ok=True)
        file_name = f'{self.taxonomic_group}-{self.uuid}.traits.xlsx'      
        return luigi.LocalTarget(output_dir / file_name)
    
    def rebuild_descriptions(self):
        """
        Delete descriptions, for a complete re-run
        """
        logger.warning('Deleting descriptions for a complete rebuild')
        for task in self.requires():
            Path(task.output().path).unlink(missing_ok=True)    
                    
class AggregateDescriptionsTask(BaseTask):    
    """
    Aggregate descriptions. Used for generating descriptions for training data etc.,

    """
        
    taxa = luigi.ListParameter()

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
        file_name = f'{self.uuid}.{OCR_MODEL.name.lower()}.descriptions.csv'
        return luigi.LocalTarget(OUTPUT_DATA_DIR / file_name)        
    

if __name__ == "__main__":    
        
    taxa = [
        'Carex binervis',
    ]
    
    task = AggregateTraitsTask(taxa=taxa, taxonomic_group=TaxonomicGroup.angiosperm, force=True)    
    task.rebuild_descriptions()
    
    luigi.build([
        task
    ], local_scheduler=True) 
    
    print('Task complete: traits written to ', task.output().path)
