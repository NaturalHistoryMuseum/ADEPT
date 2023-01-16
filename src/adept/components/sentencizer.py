
from adept.components.base import BaseComponent

class Sentencizer(BaseComponent):
    
    """
    Sentencizer, to split sentences on semicolons and periods.
    
    NB: If we just add is_sent_start for each semicolon, the default
    parser will split incorrectly
    """
    
    name = 'custom_sentencizer'

    pipeline_config = {'first': True}

    def __call__(self, doc):
        
        for token in doc[1:]:
            if self._is_sent_end(doc, doc[token.i - 1]):
                token.is_sent_start = True
            else:
                token.is_sent_start = False
                
        return doc
    
    def _is_sent_end(self, doc, token):
        return any([
            self._is_semicolon(doc, token),
            self._is_period(doc, token),
        ])
    
    @staticmethod
    def _is_semicolon(doc, token):
        return token.text == ";"
    
    @staticmethod
    def _is_period(doc, token):
        next_token = doc[token.i + 1]                
        # Ensure the next word starts with a capital or a number         
        return token.text == "." and (next_token.shape_.startswith('X') or next_token.shape_.startswith('d')) 