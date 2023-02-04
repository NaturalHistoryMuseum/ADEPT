import luigi 
import yaml
from abc import ABC, abstractmethod,ABCMeta


from adept.tasks.base import BaseTask


class BaseDescriptionTask(BaseTask, metaclass=ABCMeta):
    
    taxon = luigi.Parameter()
    
    @abstractmethod
    def get_taxon_description(self):
        return None  
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        Identifier to include in the description output
        """
        return None               
        
    def run(self):                
        description = self.get_taxon_description()   
        data = [{
            'text': description,
            'taxon': self.taxon,
            'source':self.source_name
        }]     
        with self.output().open('w') as f:
            f.write(yaml.dump(data, explicit_start=True, default_flow_style=False)) 