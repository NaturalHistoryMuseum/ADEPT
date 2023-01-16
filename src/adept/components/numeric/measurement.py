import re
from spacy.matcher import Matcher
from spacy.tokens import Span, Token
from spacy.util import filter_spans
from pint.errors import UndefinedUnitError

from adept.components.base import BaseComponent
from adept.config import unit_registry, logger

class NumericMeasurement(BaseComponent):
    
    """
    
    Match on QUANTITY and CARDINAL containing CM, MM, M, and set the measurement_unit
    

    Returns:
        doc: doc object with measurement_unit extension
    """
    
    # Has to come after dimensions, so any conjoined dimensions are split   
    pipeline_config = {'after': 'numeric_dimensions'}
       
    name = 'numeric_measurements'

    def __init__(self, nlp):                 

        super().__init__(nlp)
        self.nlp = nlp
        self.matcher = Matcher(nlp.vocab)
        
        measurement_regex = r'^cm$|^mm$|^m$'  
        volume_regex = r'^mm³$|^mm3$|^cm³$|^cm3$'
        
        self.matcher.add('MEASUREMENT', [[{"ENT_TYPE": "QUANTITY", "OP": "+"}, {"LOWER": {"REGEX": measurement_regex}}]]) 
        self.matcher.add('MEASUREMENT', [[{"ENT_TYPE": "CARDINAL", "OP": "+"}, {"LOWER": {"REGEX": measurement_regex}}]])        
        self.matcher.add('VOLUME', [[{"ENT_TYPE": "QUANTITY", "OP": "+"}, {"LOWER": {"REGEX": volume_regex}}]]) 
        self.matcher.add('VOLUME', [[{"ENT_TYPE": "CARDINAL", "OP": "+"}, {"LOWER": {"REGEX": volume_regex}}]])
         
        Span.set_extension("measurement_unit", default=None, force=True)
        Span.set_extension("measurements", default=[], force=True)
        Span.set_extension("volume_measurements", default=[], force=True)
        Token.set_extension("is_measurement", default=False, force=True)

    def __call__(self, doc):

        # Filter span, removes overlaps and preferring longest span         
        span_matches = filter_spans([
            Span(doc, start, end, self.nlp.vocab.strings[match_id]) for match_id, start, end in self.matcher(doc)
        ])
        
        for span in span_matches:
            # Unit will always be the last token as per the matcher pattern
            unit_token = span[-1]
            # Pint does not allow cm3 for cubed characters, so convert to ³: cm3 => cm³
            unit_token_lemma = re.sub('3$', '³', unit_token.lemma_)
            try:           
                unit = getattr(unit_registry, unit_token_lemma)
            except UndefinedUnitError:
                logger.error(f'Unit {unit_token_lemma} is not defined in pint')
            else:
                span._.measurement_unit = unit    
                if span.label_ == 'MEASUREMENT':
                    span.sent._.measurements.append(span)
                elif span.label_ == 'VOLUME':
                    span.sent._.volume_measurements.append(span)
                    
            for token in span:
                token._.is_measurement = True                     

        return doc 
    
import spacy    
    
    
if __name__ == '__main__':
    
    nlp = spacy.load("en_core_web_trf")

    ner = NumericMeasurement(nlp)

    text = 'Seed ovoid to ellipsoid, 1.5-2 x 1.7-2.2 cm, apex impressed 3mm³ and long. Seed volume is about 3 cm3.' 

    doc = nlp(text)
    ner(doc)

