import luigi
import pandas as pd
import numpy as np
import re
from pandas.api.types import is_numeric_dtype
from pathlib import Path
import itertools
from abc import ABC, abstractmethod,ABCMeta

from adept.config import taxonomic_groups, logger, OUTPUT_DATA_DIR, DATA_DIR, INTERMEDIATE_DATA_DIR, INPUT_DATA_DIR
from adept.tasks.pipeline import PipelineTask
from adept.tasks.base import BaseTask
from adept.utils.helpers import list_uuid
  
                     
              
class RunTask(BaseTask):              
                     
    taxa = luigi.ListParameter()
    taxonomic_group = luigi.OptionalChoiceParameter(choices=taxonomic_groups, var_type=str) 
    num_unit_regex = re.compile('([\d\.]+)\s([a-z]+)')
    
    def requires(self):
        for taxon in self.taxa:
            yield PipelineTask(taxon=taxon, taxonomic_group=self.taxonomic_group)      

    def run(self):
        
        dfs = []    
        combined_dfs = []

        for input_json in self.input():        
            df = pd.read_json(input_json.path)
            if not df.empty:
                combined = df.groupby('taxon').agg(self._series_merge).reset_index()
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
        
        with pd.ExcelWriter(self.output().path) as writer:    
            combined_dfs.to_excel(writer, sheet_name="combined", index=False)
            for source, group in dfs.groupby('source'):
                # If we don't have any values in a row, drop it         
                group = group.dropna(subset=cols, how="all")               
                if not group['source_id'].any(): group.drop('source_id', axis=1, inplace=True)
                # Ensure taxon is first column 
                ordered_cols = list(dict.fromkeys(['taxon'] + group.columns.tolist()))               
                group.to_excel(writer, sheet_name=source, index=False, columns=ordered_cols)  
                                
    def _series_merge(self, rows):
        # Remove any empty rows     
        rows = rows[rows.notnull()]
            
        if rows.empty:
            return
        
        if is_numeric_dtype(rows):
            return rows.mean().round(2)
        
        num_unit = [g for row in rows if (g := self.num_unit_regex.match(row))]
        
        if num_unit:
            num = np.array([float(n.group(1)) for n in num_unit]).mean().round(2)
            unit = num_unit[0].group(2)   
            return f'{num} {unit}'
        
        # Ploidy 2n contains , so we don't want to split or concatenate on ','     
        text_list = [s.split(',') for s in rows if not s.startswith('2n')]
        if text_list:
            return ', '.join(set([t.strip() for t in itertools.chain(*text_list)]))
        else:
            return '| '.join(rows)     

        
    def output(self):
        uuid = list_uuid(self.taxa)    
        file_name = f'{self.taxonomic_group}-{uuid}.traits.xlsx'        
        return luigi.LocalTarget(OUTPUT_DATA_DIR / file_name)
                    
       
    

if __name__ == "__main__":    
    
    input_file = INPUT_DATA_DIR / 'north-american-assessments.csv'
    df = pd.read_csv(input_file)
    
    taxa = df['scientificName'].unique().tolist()   
    # taxa = taxa[:10]
    
    taxa = [
        'Aquilaria malaccensis, Brachystegia oblonga, Dracula lemurella, Ateleia popenoei, Ocotea monteverdensis, Puya lopezii, Trichosalpinx inquisiviensis, Auerodendron reticulatum, Koanophyllon tetranthum, Acca lanuginosa, Stelis hirtella, Oxyspora cernua, Pilosella procera, Alpinia jianganfeng',
        'Melaleuca accedens'
    ]
    
    # print(taxa)
    

    
    # taxon = 'Leersia hexandra'
    # taxa = [taxon]
    
    # luigi.build([PipelineTask(taxon=taxon, taxonomic_group='angiosperm', force=True)], local_scheduler=True)  
    
    # luigi.build([AggregateTask(taxa=taxa, taxonomic_group='angiosperm', force=True)], local_scheduler=True)  
    
    luigi.build([AggregateFileTask(taxa=taxa, taxonomic_group='angiosperm', force=True)], local_scheduler=True) 
