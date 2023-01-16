import csv
import spacy
from fractions import Fraction

from spacy.matcher import Matcher
from spacy.tokens import Token


from adept.components.base import BaseComponent


class NumericFraction(BaseComponent):
    
    """
    Match x / y
    
    Set fraction value
    """
    
    name = "numeric_fraction"
    
    def __init__(self, nlp):                 
        super().__init__(nlp)  
        
        self.matcher = Matcher(nlp.vocab)        
        self.matcher.add('FRACTION', [[{"TEXT": {"REGEX": "^[0-9+]/[0-9+]$"}}]]) 
        
        Token.set_extension("fraction", default=False, force=True)  

    def __call__(self, doc):

        for _, start, end in self.matcher(doc):
            token = doc[start]

            try:            
                fraction_value = float(Fraction(token.text))
            except ValueError:
                # Ignore value errors - could be part of a range or have extra chars
                pass
            else:
                token._.set("fraction", fraction_value)             
            
        return doc