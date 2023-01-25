import re
from tokenize import Token
from spacy.matcher import Matcher
from spacy.tokens import Span

from adept.utils.helpers import token_get_ent
from adept.config import logger


class NumericRangeComponent: 
    
    """
    
    Match on 'MEASUREMENT', 'DIMENSION', 'CARDINAL', 'VOLUME' ents containing range characters (, -, +)
    
    Parses the range into a dict with keys: lower, from, to, upper
    

    Returns:
        doc: doc object with range, is_range extension
    """
    
    name = 'numeric_range'
    
    re_range = re.compile('((?P<lower>[0-9.\/]+)\-?\))?\s?(?P<from>[0-9.\/]+)[\(\)\s]?\-[\(\)\s]?(?P<to>[0-9.\/]+)\s?(\(\-?(?P<upper>[0-9.\/]+))?')
    
    def __init__(self, nlp):
        self.matcher = Matcher(nlp.vocab) 
        # Matcher for (, ) or -, contained within QUANTITY or CARDINAL entity type   
        for ent_type in ['MEASUREMENT', 'DIMENSION', 'CARDINAL', 'VOLUME']:
            self.matcher.add('RANGE', [[{"ENT_TYPE": ent_type}, {"LOWER": {"REGEX": r'^-|\(\)$'}}]])        
                
        Span.set_extension("numeric_range", default=[], force=True)
        # Token.set_extension("is_numeric_range", default=False, force=True)
    
    def __call__(self, doc):

        for _, start, end in self.matcher(doc):
            
            token = doc[start]
            # Get the entire ent for token - matcher is just for -             
            ent = token_get_ent(token)

            matches = self.re_range.finditer(ent.text)
            for match in matches:
                try:
                    numeric_range = match.groupdict()
                except AttributeError:
                    logger.error("Error parsing range %s in %s", ent, ent.sent)                 
                else:
                    # Set range dict on the span
                    ent._.set("numeric_range", numeric_range)  
                    # Fixme - do I need this??                 
                    # [token._.set('is_numeric_range', True) for token in ent]

        return doc
    
    
