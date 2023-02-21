import spacy
from spacy.language import Language
import enum

from spacy.tokens import Doc, Span
from spacy.matcher import Matcher
from spacy.util import filter_spans
from adept.config import DimensionType

class MeasurementDimensionRelationComponent:
    
    """
    Create relations between measurements and dimension entities
    
    Maches on MEASUREMENT -> a-z {0, MAX_TOKEN_DISTANCE} -> DIMENSION
    
    e.g. 2 cm in diameter  3 - 5 cm long
    
    """
    
    def __init__(self, nlp: Language):   
        self.nlp = nlp
        self.matcher = Matcher(nlp.vocab)    
        
        MAX_TOKEN_DISTANCE = 1
        
        for dimension in DimensionType:        
            self.matcher.add(dimension.name, [[{"ENT_TYPE": "MEASUREMENT", "OP": "+"}, {"IS_ALPHA": True, "OP": f"{{,{MAX_TOKEN_DISTANCE}}}"}, {"ENT_TYPE": dimension.name}]]) 
            
        Span.set_extension("measurement_dimension", default=None, force=True) 

    def __call__(self, doc: Doc) -> Doc:
        
        # Filter span, removes overlaps and preferring longest span         
        span_matches = filter_spans([
            Span(doc, start, end, self.nlp.vocab.strings[match_id]) for match_id, start, end in self.matcher(doc)
        ])
        
        for span in span_matches:
            dimension = next((ent for ent in span.ents if ent.label_ == span.label_), None)
            measurement = next((ent for ent in span.ents if ent.label_ == 'MEASUREMENT'), None)            
            measurement._.set("measurement_dimension", dimension)
            
        return doc