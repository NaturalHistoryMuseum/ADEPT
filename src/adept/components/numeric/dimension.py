from spacy.matcher import Matcher
from spacy.tokens import Span, Token
from spacy.util import filter_spans

from adept.components.base import BaseComponent
from adept.utils.helpers import token_get_ent

class NumericDimension(BaseComponent):
    
    """    
    Match on CARDINAL or QUANTITY entities, containing x or by
    
        a) Adds dimensions extension to the whole span
        b) Splits the CARDINAL or QUANTITY entity into two - this is required so
           measurement/range extensions can be correctly identified 
        

    Returns:
        doc: doc object with added dimension extension
    """
    
    name = 'numeric_dimensions'
    
    pipeline_config = {'after': 'numeric_expand'}
    
    def __init__(self, nlp):
        super().__init__(nlp)
        self.matcher = Matcher(nlp.vocab) 
        # Matcher for x or by, contained within QUANTITY or CARDINAL entity type         
        self.matcher.add('DIMENSION', [[{"ENT_TYPE": "QUANTITY"}, {"LOWER": {"REGEX": f'^x|by$'}}]]) 
        self.matcher.add('DIMENSION', [[{"ENT_TYPE": "CARDINAL"}, {"LOWER": {"REGEX": f'^x|by$'}}]])        
        
        Span.set_extension("dimensions", default=[], force=True)
        Token.set_extension("is_dimension", default=False, force=True)
    
    def __call__(self, doc):
        
        ents = list(doc.ents)

        for _, start, end in self.matcher(doc):
            
            token = doc[start]
            spans= []
            
            # Get the entire ent for token             
            ent = token_get_ent(token)
            
            # Is the end of the ent beyond the x | by - if so, it needs splitting
            if ent.end > end:
                token.sent._.dimensions.append(ent)

                # We want to remove the long ent, so dimensions works properly 
                try:
                    ents.remove(ent)
                except ValueError:
                    pass                     
                            
                split_point = ent.start + list(ent).index(token) + 1
                
                # Split the ent into two
                spans = [
                    Span(doc, ent.start, split_point, label=ent.label_),
                    Span(doc, split_point + 1, ent.end, label=ent.label_)
                ]
                
                ents.extend(spans)
            # The next ent is part of the dimension, but hasn't been included in the ent
            else:
                # FIXME: Need to handle better ent being at end of doc
                # IndexError: [E040] Attempt to access token at 228, max length 227.
                # FIXME: Amelanchier cusickii
                try:
                    sibling_ent = token_get_ent(doc[end+1], ['QUANTITY', 'CARDINAL'])
                except IndexError:
                    pass
                else:
                    
                    if sibling_ent:                
                        spans = [ent, sibling_ent]
                        token.sent._.dimensions.append(Span(doc, ent.start, sibling_ent.end))
                    
            for span in spans:
                for token in span:
                    token._.is_dimension = True 

        doc.ents = filter_spans(ents)
        return doc