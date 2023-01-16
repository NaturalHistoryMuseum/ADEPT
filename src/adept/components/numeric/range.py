import re
from tokenize import Token
from spacy.matcher import Matcher
from spacy.tokens import Span

from adept.components.base import BaseComponent
from adept.utils.helpers import token_get_ent
from adept.config import logger

class NumericRange(BaseComponent): 
    
    """
    
    Match on QUANTITY and CARDINAL containing range characters (, -, +)
    
    Parses the range into a dict with keys: lower, from, to, upper
    

    Returns:
        doc: doc object with range, is_range extension
    """
    
    name = 'numeric_range'
    
    re_range = re.compile('((?P<lower>[0-9.\/]+)\-?\))?\s?(?P<from>[0-9.\/]+)[\(\)\s]?\-[\(\)\s]?(?P<to>[0-9.\/]+)\s?(\(\-?(?P<upper>[0-9.\/]+))?')
    
    def __init__(self, nlp):
        super().__init__(nlp)
        self.matcher = Matcher(nlp.vocab) 
        # Matcher for (, ) or -, contained within QUANTITY or CARDINAL entity type   
        for ent_type in ['QUANTITY', 'CARDINAL']:
            self.matcher.add('RANGE', [[{"ENT_TYPE": ent_type}, {"LOWER": {"REGEX": r'^-|\(\)$'}}]])        
                
        Span.set_extension("numeric_range", default=[], force=True)
        # Token.set_extension("is_numeric_range", default=False, force=True)
    
    def __call__(self, doc):

        for _, start, end in self.matcher(doc):
            token = doc[start]
            # Get the entire ent for token             
            ent = token_get_ent(token)
            
            match = self.re_range.search(ent.text)
            
            try:
                numeric_range = match.groupdict()
            except AttributeError:

                # TODO: Regex is confusing +-, but let's ignore for now   
                if '+-' in ent.text:   
                    continue
                # FIXME Last character is the dash - FIXME in regex 
                if ent[-1].text == '-':
                    continue
                
                # FIXME Is this 3-toothed? 
                if re.match('^[0-9]+\-[a-z]+$', ent.text):
                    continue
                    
                logger.error("Error parsing range %s in %s", ent, ent.sent)                 

                # raise Exception
                    
            else:
                # Set range dict on the span
                ent._.set("numeric_range", numeric_range)      
                # Fixme - do I need this??                 
                # [token._.set('is_numeric_range', True) for token in ent]
                
        return doc