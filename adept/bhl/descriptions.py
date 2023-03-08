import re
from taxonerd import TaxoNERD
import re
from taxonerd import TaxoNERD
from spacy.tokens import Doc
from spacy.tokens import Span

from adept.bhl.preprocess import BHLPreprocess
from adept.worldflora import WorldFlora
from adept.bhl.model import TextClassifier
from adept.config import logger

class BHLDetectDescriptions():
    
    # Match 15a. etc., at start of string
    re_figure=re.compile('^[0-9]+[a-zA-Z][.|\s]') 
     
    wf = WorldFlora()
    taxonerd = TaxoNERD(prefer_gpu=False)
    nlp = taxonerd.load(model="en_core_eco_biobert", exclude=["pysbd_sentencizer"])    
    preprocess = BHLPreprocess()
    text_classifier = TextClassifier()
    
    MINIMUM_WORD_COUNT = 50
    
    def __init__(self, taxon: str):
        self._re_names = self._name_match_regex(taxon)

    def _name_match_regex(self, taxon: str):
        names = set([taxon])
        if synonyms := self.wf.get_related_names(taxon):
            names |= synonyms        

        logger.debug('Using name and synonyms %s for taxon %s', names, taxon)
        # Add pattern Genus species => G. species
        names |= {r'{0}\.\s{1}'.format(n[0][0],n[1]) for name in names if (n := name.split())}
        names_pattern = '|'.join(names)
        return re.compile(fr'{names_pattern}', re.IGNORECASE)
        
    def __call__(self, text: str):
        text = self.preprocess(text)
        doc = self.nlp(text)  
        doc.ents = self._segment_ents(doc)
        return list(self._get_descriptions(doc))
        
    def _get_descriptions(self, doc):
        
        doc_matching_ents = [e for e in doc.ents if e.label_ == 'MATCHING_LIVB']
        seen_matches = []

        # If there's no matching taxa ents
        if not doc_matching_ents:
            return
    
        is_name_match = False
        for para in self._doc_to_paragraphs(doc):
            
            if self._is_figure(para.text):
                # logging.debug(f"IS FIGURE: {paragraph}")
                continue            
            
            if para.ents:
                para_matching_ents = [e for e in para.ents if e.label_ == 'MATCHING_LIVB']
                seen_matches.extend(para_matching_ents)
                is_name_match = True if para_matching_ents and len(para_matching_ents) == len(para.ents) else False        
                # Exit as soon as we've seen all the matching names in the doc
                # But only once we no longer have a name match - allows a name match
                # and then continue to loop through subsequent paras         
                if not is_name_match and len(seen_matches) >= len(doc_matching_ents):
                    break

            if not is_name_match:
                continue

            if len(para) <= self.MINIMUM_WORD_COUNT:
                continue

            if not self._paragraph_is_description(para):
                continue

            logger.debug(f"Description found for %s", para_matching_ents)           
            yield para.text   
            
    @staticmethod
    def _doc_to_paragraphs(document: Doc) -> Span:
        start = 0
        for token in document:
            if token.is_space and token.text.count("\n") > 1:
                yield document[start:token.i]
                start = token.i
                
        yield document[start:]

    @staticmethod
    def _is_well_formed_name(taxon_name) -> bool:
        # If a taxa is all upper case (model has misidentified an acronym) or doesn't start with a capital
        return taxon_name[0].isupper() and not taxon_name.isupper()
    
    def _is_figure(self, paragraph: str) -> bool:
        return bool(self.re_figure.match(paragraph))     
    
    def _segment_ents(self, doc: Doc):
        def _get_labelled_ent(ent):
            label = 'MATCHING_LIVB' if self._re_names.search(ent.text) else 'LIVB'
            return Span(ent.doc, ent.start, ent.end, label=label)
    
        return [_get_labelled_ent(ent) for ent in doc.ents if ent.label_ == 'LIVB' and self._is_well_formed_name(ent.text)]        

    def _paragraph_is_description(self, para: str) -> bool:
        return self.text_classifier(para.text)  