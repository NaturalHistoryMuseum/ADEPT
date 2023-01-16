from abc import ABC, abstractmethod


class BaseComponent(ABC):
    
    pipeline_config = {}

    @property
    @abstractmethod
    def name(self):
        return None   
    
    def __init__(self, nlp): 
        print(f"INIT {self.name}")       