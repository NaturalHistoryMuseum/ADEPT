import csv

import spacy
from spacy.language import Language
from spacy.tokens import Doc
from spacy.matcher import Matcher
from spacy.tokens import Span, Token
from spacy import displacy
from spacy.pipeline import EntityRuler
from pathlib import Path
from spacy.util import filter_spans

from adept.utils.expand import ExpandSpan
from adept.utils.helpers import token_get_ent
from adept.tasks.patterns.trait import TraitPatternsTask

# class DiscreteTraitsComponent(EntityRuler):
          
#     patterns_file_path =  TraitPatternsTask().output().path

#     def __init__(self, nlp, *args, **cfg):
#         super().__init__(nlp, overwrite_ents=True, *args, **cfg)
        
#         self.from_disk(self.patterns_file_path)
        
        
class CustomTraitsComponent:  
    
    def __init__(self, nlp):                 

        self.matcher = Matcher(nlp.vocab)   
        self.matcher.add('PLOIDY LEVEL (2n)', [[{"LOWER": "2n"}, {"LOWER": "="}]], on_match=self.on_ploidy_match)
        self.matcher.add('PLOIDY LEVEL (2n)', [[{"TEXT": {"REGEX": "2n="}}]], on_match=self.on_ploidy_match)
        # FIXME: Is merosity still used? It should be covered by the new measurements. 
        self.matcher.add('MEROSITY', [[{"POS": "NUM"}, {"LOWER": "-"}, {"LOWER": "merous"}]], on_match=self.on_merosity_match)
        
        self.expand_ploidy = ExpandSpan(
            ['=', ','], 
            pos_tags=['NUM']
        )
        Span.set_extension("trait_value", default=None, force=True)

    def __call__(self, doc):
        self.ents = set(doc.ents)
        self.matcher(doc)
        doc.ents = filter_spans(list(self.ents))
        return doc  
        
    def on_ploidy_match(self, matcher, doc, i, matches): 
        match_id, start, end = matches[i]
        token = doc[start]
        span = self.expand_ploidy(doc, token)       
        self._add_ent(doc, span.start, span.end, match_id)
                
    def on_merosity_match(self, matcher, doc, i, matches): 
        match_id, start, end = matches[i]
        self._add_ent(doc, start, end, match_id)
        pass
    
    def _add_ent(self, doc, start, end, match_id):
        string_id = self.matcher.vocab.strings[match_id]
        entity = Span(doc, start, end, label=string_id)                
        overlapping = {ent for token in entity if (ent := token_get_ent(token))}
        # Rather than relying on filter_spans, explicity remove existing ents on the tokens
        # otherwise some CARDINAL ents will be longer and preferred to ploidy level
        self.ents = self.ents.difference(overlapping)        
        entity._.set("trait_value", entity.text)                   
        self.ents.add(entity)            