import luigi
import pandas as pd
import numpy as np
import re
from luigi import parameter

from adept.config import RAW_DATA_DIR, taxonomic_groups, logger
from adept.tasks.pipeline import PipelineTask

class AggregateTask(luigi.Task):
    taxon = luigi.Parameter()  
    taxonomic_group = luigi.ChoiceParameter(choices=taxonomic_groups, var_type=str, default="angiosperm") 
    
    def run(self):
        # print('HHHH')
        logger.error('RUN')
        
    def requires(self):
        return [
            PipelineTask(taxon=self.taxon, taxonomic_group=self.taxonomic_group)
        ]
    

class AggregateFileTask(luigi.Task):
    
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

    def requires(self):
        for taxon, taxon_group in self._read_names_from_file():
            taxon_group = taxon_group.lower()
            if not taxon_group in taxonomic_groups: 
                raise Exception('Unknown taxonomic group %s - must be one of %s '% (taxon_group, ' '.join(taxonomic_groups)))

            yield AggregateTask(taxon=taxon, taxonomic_group=taxon_group)
    
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
    
    
if __name__ == "__main__":    
    luigi.build([AggregateTask(taxon="Prunus cerasifera")], local_scheduler=True)      