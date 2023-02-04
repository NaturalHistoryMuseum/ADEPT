import enum
from spacy.tokens import Span, Token, Doc

class ExpandSpan():
    
    """
    Expand span, so it incorporates neighbouring tokens with characters or pos_tag
    """
    
    class Direction(enum.Enum):
        FORWARD = 1
        BACKWARD = -1     
    
    def __init__(self, characters: list, pos_tags: list = None, entity_types: list = None):
        self.characters = characters
        self.pos_tags = pos_tags if pos_tags else []
        self.entity_types = entity_types if entity_types else []
        
    def __call__(self, doc: Doc, token: Token):
        end_token = self._expand(doc, token, direction=self.Direction.FORWARD)
        start_token = self._expand(doc, token, direction=self.Direction.BACKWARD)
        return Span(doc, start_token.i, end_token.i + 1) 
    
    def _expand(self, doc: Doc, token: Token, direction):    
        i = token.i
        while True:
            next_i = i + direction.value
            
            # Do not look beyond the edges of the doc
            if next_i >= len(doc) or next_i < 0:
                break

            next_token = doc[next_i]            
            if self._is_matching_token(next_token):
                # Fix 6-65+ cm (usually rhizomatous                 
                if direction==self.Direction.FORWARD and next_token.text == '(' and not self._is_matching_token(doc[next_token.i + direction.value]):
                    break
                    
                i = next_token.i
            else:
                break
        
        return doc[i]
    
    def _is_matching_token(self, token: Token):
        return token.lower_ in self.characters or token.pos_ in self.pos_tags or token.ent_type_ in self.entity_types 
