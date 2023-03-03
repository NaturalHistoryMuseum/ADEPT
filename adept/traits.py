import pandas as pd
import sqlite3
import uuid
import yaml
import numpy as np

from adept.config import ASSETS_DIR
from adept.utils.helpers import get_words

class Traits():
    """ 
    Read the traits from functional traits database
    """
    
    _df = pd.read_parquet(ASSETS_DIR / 'traits.parquet') 
            
    def get_discrete_traits(self, group=None):     
        return self._get_traits_by_type('discrete', group) 
    
    def get_colour_traits(self, group=None):
        return self._get_traits_by_type('colour', group)    
    
    def get_unique_colour_terms(self, group=None):
        df = self.get_colour_traits(group)
        return df.term.unique()   
    
    def get_unique_discrete_terms(self, group=None):
        df = self._get_traits_by_type('discrete', group)
        # Use both terms and character values - if a character exists in the text
        # we want tofind and use it
        return np.concatenate([df.term.unique(), df.character.unique()])
                    
    def _get_traits_by_type(self, trait_type, group = None):
        mask = (self._df.type == trait_type)
        if group:
            mask &= (self._df.group == group)
        return self._df[mask]        
                    
    
        

class SimpleTraitTextClassifier:    
    """
    Quick method to classify text as a description
    """
    
    traits = Traits()
        
    def __init__(self, min_terms=5, min_chars=100, min_ratio=None):        
        self.min_terms = min_terms
        self.min_ratio = min_ratio
        self.min_chars = min_chars
        self._trait_terms = set([term.lower() for term in self.traits.get_unique_discrete_terms()])
        
    def is_description(self, text):
        if len(text) < self.min_chars:
            return False
        
        words = text.lower().split()
        
        matching_terms = self._trait_terms.intersection(words)
        
        ratio = len(matching_terms) / len(words) 
        
        if len(matching_terms) < self.min_terms:
            return False     
        
        if self.min_ratio and len(matching_terms) / len(words)  < self.min_ratio:
            return False
        
        return True   
                 
   
if __name__ == '__main__':
    traits = SimpleTraitTextClassifier()
    
    
    text = "Herbs to 50 cm tall, annual, much branched. Stems 4-angled, glabrous. Petiole 0.3-1 cm; leaf blade ovate-lanceolate, lanceolate, or narrowly elliptic, 1.5-7 × 1-2.5 cm, both surfaces glabrous, abaxially pale green, adaxially green, secondary veins 3-5 on each side of midvein, base attenuate and decurrent onto petiole, margin entire, apex acute to shortly acuminate."
    print(traits.is_description(text))
    
