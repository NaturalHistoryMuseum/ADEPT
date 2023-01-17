import luigi
import pandas as pd
import numpy as np
import re
from luigi import parameter
from pandas.api.types import is_numeric_dtype
from pathlib import Path
import itertools
import uuid
import pickle
from abc import ABC, abstractmethod,ABCMeta

from adept.config import RAW_DATA_DIR, taxonomic_groups, logger, PROCESSED_DATA_DIR
from adept.tasks.pipeline import PipelineTask
from adept.tasks.base import BaseTask

class AggregateBaseTask(BaseTask, metaclass=ABCMeta):
    
    num_unit_regex = re.compile('([\d\.]+)\s([a-z]+)')
    
    @abstractmethod
    def _get_taxa_and_group(self):
        return None  
            
    def requires(self):
        for taxon, taxon_group in self._get_taxa_and_group():
            yield PipelineTask(taxon=taxon, taxonomic_group=taxon_group)  
                      
    def run(self):
        
        dfs = []    
        combined_dfs = []

        for input_json in self.input():
            input_json_path = Path(input_json.path)
            taxon = input_json_path.stem.replace('-', ' ').capitalize()
            df = pd.read_json(input_json_path)
            df.insert(0, 'taxon', taxon)
            combined = df.groupby('taxon').agg(self._series_merge).reset_index()
            dfs.append(df)
            combined_dfs.append(combined)            
            
        combined_dfs = pd.concat(combined_dfs)
        combined_dfs = combined_dfs.drop(columns='source')
        dfs = pd.concat(dfs)
        cols = set(dfs.columns).difference(set(['taxon', 'source']))
        combined_dfs = combined_dfs.dropna(subset=cols, how="all")   
        
        with pd.ExcelWriter(self.output().path) as writer:    
            combined_dfs.to_excel(writer, sheet_name="combined", index=False)
            for source, group in dfs.groupby('source'):
                sheet_name = source.replace('/', '-')
                # If we don't have any values in a row, drop it         
                group = group.dropna(subset=cols, how="all")
                group.to_excel(writer, sheet_name=sheet_name, index=False)  
                
                
    def _series_merge(self, rows):
        # Remove any empty rows     
        rows = rows[rows.notnull()]
            
        if rows.empty:
            return
        
        if is_numeric_dtype(rows):
            print("HSHSHSHSHSSH")
            print(rows)
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
                     
              
class AggregateTask(AggregateBaseTask):              
                     
    taxon_names = luigi.ListParameter()
    taxonomic_group = luigi.OptionalChoiceParameter(choices=taxonomic_groups, var_type=str) 

    def _get_taxa_and_group(self):
        for taxon in self.taxon_names:
            yield taxon, self.taxonomic_group

    @property           
    def uuid(self):
        """
        Create a uuid from the names list to use as a unique file output name
        """
        return uuid.uuid5(uuid.NAMESPACE_URL, str(pickle.dumps(self.taxon_names))).hex 
        
    def output(self):
        return luigi.LocalTarget(PROCESSED_DATA_DIR / f'{self.uuid}.traits.xlsx')                  
                    
class AggregateFileTask(AggregateBaseTask):
    
    file_path = luigi.PathParameter(exists=True, default=RAW_DATA_DIR / 'species-example.csv')
    taxon_column = luigi.Parameter(default='Species name')
    taxon_group_column = luigi.OptionalStrParameter(default=None)
    taxonomic_group = luigi.OptionalChoiceParameter(choices=taxonomic_groups, var_type=str, default=None)  
 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self._validate_group_paramters(*args, **kwargs)
        
    def _validate_group_paramters(self, *args, **kwargs):
        """
        Ensure we have either taxonomic group column or taxonomic group set
        """
        params = self.get_params()
        param_values = dict(self.get_param_values(params, args, kwargs))
        group_params = ['taxonomic_group', 'taxon_group_column']
        group_param_values = [param_values.get(p) for p in group_params]
        task_family = self.get_task_family()
        exc_desc = '%s[args=%s, kwargs=%s]' % (task_family, args, kwargs)        
        if not any(group_param_values):
            raise parameter.MissingParameterException("%s: requires one of '%s' to be set" % (exc_desc, ' '.join(group_params)))
        elif all(group_param_values):
            raise parameter.DuplicateParameterException("%s: requires only one of '%s' to be set" % (exc_desc, ' '.join(group_params)))    

    
    def _get_taxa_and_group(self):
        for taxon, taxon_group in self._read_names_from_file():
            taxon_group = taxon_group.lower()
            if not taxon_group in taxonomic_groups: 
                raise Exception('Unknown taxonomic group %s - must be one of %s '% (taxon_group, ' '.join(taxonomic_groups)))
            
            yield taxon, taxon_group
    
    def _read_names_from_file(self):        
        df = self._read_file()
        
        if self.taxon_group_column:
            yield from df[[self.taxon_column, self.taxon_group_column]].drop_duplicates().values.tolist()
        else:
            taxa = df[self.taxon_column].unique()
            yield from list(zip(taxa, [self.taxonomic_group] * len(taxa)))
  
    def _read_file(self):
        
        if self.file_path.suffix == '.csv':
            return pd.read_csv(self.file_path)
        elif self.file_path.suffix  in ['.xlsx']:
            return pd.read_excel(self.file_path)
        
        raise Exception('Only .csv and .xslx files are supported')
            
    def output(self):
        output_file_name = Path(self.file_path).stem
        return luigi.LocalTarget(PROCESSED_DATA_DIR / f'{output_file_name}.traits.xlsx')           
    
    
    
    
if __name__ == "__main__":    
    luigi.build([AggregateTask(taxon_names=["Hedychium brevicaule"], taxonomic_group='angiosperm', force=True)], local_scheduler=True)    
    # luigi.build([AggregateFileTask(taxonomic_group='angiosperm', force=True)], local_scheduler=True)