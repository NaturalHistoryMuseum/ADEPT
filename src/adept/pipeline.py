import spacy

from adept.components.registry import ComponentsRegistry
from adept.components.sentencizer import Sentencizer
from adept.components.numeric import (NumericDimension, NumericExpand, NumericFraction, NumericMeasurement, NumericRange)
from adept.components.anatomical import AnatomicalEntity
from adept.components.traits import DiscreteTraitsEntity
from adept.components.traits import CustomTraitsEntity
from adept.preprocess import Preprocess
from adept.postprocess import Postproccess


class Pipeline():
    
    def __init__(self):

        self.nlp = spacy.load("en_core_web_trf")
        
        registry = ComponentsRegistry(self.nlp)
        registry.add_components([
            Sentencizer,
            AnatomicalEntity,
            DiscreteTraitsEntity,
            CustomTraitsEntity,
            NumericExpand,
            NumericDimension,
            NumericMeasurement,
            NumericRange,
            NumericFraction,
        ])
        
        self.preprocess = Preprocess()        
        self.postprocess = Postproccess()  

    
    def __call__(self, text, taxon_group):  
        
        text = self.preprocess(text)          
        doc = self.nlp(text)
        return self.postprocess(doc, taxon_group)
    

