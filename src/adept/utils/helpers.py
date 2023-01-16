from collections.abc import MutableMapping
import pandas as pd
import re


def get_variety_higher_taxa(name):
    # Regex to match species name before var. or subsp.  
    return re.match('^[a-zA-Z\s]+(?=(\svar\.|\ssubsp\.))', name).group(0)

def split_string_on_whitespace(text):
    # find all words, seperated by whitespace or punctuation  
    re_whitespace = re.compile(r"[\w'\"]+|[,.!?]") 
    return re_whitespace.findall(text)

def get_words(text):
    return re.compile('\w+').findall(text)

def token_get_ent(token, ent_types=None):
    if token.ent_type_:
        for ent in token.doc.ents:
            if ent_types and ent.label_ not in ent_types: continue
            if ent.start <= token.i < ent.end:
                return ent        
            
def flatten_dict(d: MutableMapping, sep: str= '.') -> MutableMapping:
    [flat_dict] = pd.json_normalize(d, sep=sep).to_dict(orient='records')
    return flat_dict            