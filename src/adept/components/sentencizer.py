import spacy
from spacy.language import Language
from spacy.tokens import Doc, Token



class SentencizerComponent:
    
    """
    Sentencizer, to split sentences on semicolons and periods.
    
    If we just add is_sent_start for each semicolon, the default
    parser will split incorrectly
    """
    
    def __init__(self, nlp: Language):
        self.nlp = nlp
    
    def __call__(self, doc: Doc) -> Doc:        
        for token in doc[:-1]:
            next_token = doc[token.i + 1]
            if self._is_semicolon(token):
                next_token.is_sent_start = True
            elif self._is_period(token):
                # period then capital: new sentence                 
                if next_token.shape_.startswith('X'):
                    next_token.is_sent_start = True
                # period then number: possibly new sentence. let the default parse evaluate it    
                elif next_token.shape_.startswith('d'):
                    next_token.is_sent_start = None
                else:
                    next_token.is_sent_start = False
            else:
                next_token.is_sent_start = False

                
        return doc

    @staticmethod
    def _is_semicolon(token) -> Token:
        return token.text == ";"
    
    @staticmethod
    def _is_period(token) -> Token:            
        return token.text == "."  