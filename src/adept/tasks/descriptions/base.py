import luigi 
from abc import ABC, abstractmethod,ABCMeta


class DescriptionTask(luigi.Task, metaclass=ABCMeta):
    
    taxon = luigi.Parameter()
    
    @property
    @abstractmethod
    def base_url(self):
        return None   
    
    @abstractmethod
    def get_taxon_description(self):
        return None         
        
    def run(self):        
        description = self.get_taxon_description()
        with self.output().open('w') as f:
            f.write(description or '')