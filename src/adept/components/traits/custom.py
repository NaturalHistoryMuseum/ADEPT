import spacy
from spacy.matcher import Matcher
from spacy.tokens import Span, Token
from spacy.util import filter_spans

from adept.components.base import BaseComponent
from adept.utils.expand import ExpandSpan

class CustomTraitsEntity(BaseComponent):  
    
    name = "custom_traits_entity"
    
    def __init__(self, nlp):                 

        super().__init__(nlp)
                
        self.matcher = Matcher(nlp.vocab)   
        self.matcher.add('PLOIDY LEVEL (2n)', [[{"LOWER": "2n"}, {"LOWER": "="}]], on_match=self.on_ploidy_match)
        self.matcher.add('MEROSITY', [[{"POS": "NUM"}, {"LOWER": "-"}, {"LOWER": "merous"}]], on_match=self.on_merosity_match)
        
        self.expand_ploidy = ExpandSpan(
            ['=', ','], 
            pos_tags=['NUM'],
            entity_types=['QUANTITY', 'CARDINAL']
        )
        Span.set_extension("trait_value", default=None, force=True)

    def __call__(self, doc):
        self.ents = list(doc.ents)
        self.matcher(doc)
        doc.ents = filter_spans(self.ents)
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
        entity._.set("trait_value", entity.text)                   
        self.ents.append(entity)    
    
    
if __name__ == '__main__':
    
    nlp = spacy.load("en_core_web_trf")

    ner = CustomTraitsEntity(nlp)

    text = 'Herbs, perennial, 40-100 cm tall, with long rhizomes; stems erect, unbranched or branched in upper part, often with short sterile branches at leaf axils above middle, striate, usually white villous. 2n = 4' 
    
    
    
    doc = nlp(text)

    doc = ner(doc)
    for ent in doc.ents:
        print(ent.label_, ent.text)
        print(ent._.get("trait_value"))