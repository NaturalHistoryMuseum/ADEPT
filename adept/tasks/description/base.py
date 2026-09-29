import luigi 
import yaml
from abc import ABC, abstractmethod,ABCMeta


from adept.tasks.base import BaseTask


class BaseDescriptionTask(BaseTask, metaclass=ABCMeta):
    
    taxon = luigi.Parameter()
    
    @abstractmethod
    def get_taxon_description(self):
        return {}  
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        Identifier to include in the description output
        """
        return None               
        
    def run(self):                
        result = self.get_taxon_description()  

        data = [{
            'text': result.get('description', None),
            'taxon': self.taxon,
            'source': self.source_name,
            'source_id': result.get('source_id', None)
        }]    

        with self.output().open('w') as f:
            f.write(yaml.dump(data, explicit_start=True, default_flow_style=False)) 