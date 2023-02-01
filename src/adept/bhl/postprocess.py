import re
from taxonerd import TaxoNERD
import logging
from spacy.tokens import Span

from adept.config import LOG_DIR
from adept.worldflora import WorldFlora
from adept.bhl.model import predict

logging.basicConfig(filename= LOG_DIR / 'descriptions.log', encoding='utf-8', level=logging.DEBUG)

class BHLPostprocess:  
    
    # Match 15a. etc., at start of string
    re_figure=re.compile('^[0-9]+[a-zA-Z][.|\s]')       
    
    
    wf = WorldFlora()
    taxonerd = TaxoNERD(prefer_gpu=False)
    nlp = taxonerd.load(model="en_core_eco_biobert")
    
    MINIMUM_WORD_COUNT = 50
    
    def __init__(self):        
        self._re_names = {}
        
    def _get_taxon_name_regex(self, taxon: str):
        # If we don't already have a compiled regex for this name, build it          
        if not self._re_names.get(taxon):
            names = set([taxon])
            if synonyms := self.wf.get_related_names(taxon):
                names |= synonyms        
            names |= {n[1] for name in names if (n := name.split())}
            names_pattern = '|'.join(names)
            self.re_names[taxon] = re.compile(fr'{names_pattern}', re.IGNORECASE)   
            
        return self._re_names[taxon]    
        
    
    def __call__(self, taxon: str, paragraphs: list[str]):
        
        re_taxon_name = self._get_taxon_name_regex(taxon)
        is_name_match = False
        
        for paragraph in paragraphs:
            
            if self._is_figure(paragraph):
                logging.debug(f"IS FIGURE: {paragraph}")
                continue
                
            if self._is_below_minimum_word_count(paragraph):
                logging.debug(f"MIN WORD COUNT: {paragraph}")
                continue
            
            if taxon_names := self._detect_taxon_names(paragraph):
                # If we have species names in the text, see if they match the species we're looking for
                # If we don't have species names, is_name_match carries over from previous loop                  
                matching_taxon_names = self._get_matching_taxon_names(re_taxon_name, taxon_names)
                # If the paragraph matches the name we're looking for, and it's the only species name in the paragraph         
                is_name_match = matching_taxon_names and (len(matching_taxon_names) == len(taxon_names))
                
            
            if not is_name_match:
                logging.debug(f"NO NAME MATCH: {paragraph}")
                continue
                
            if not self._classify_paragraph_is_description(paragraph):
                logging.debug(f"NOT DESCRIPTION: {paragraph}")
                continue
                
            print()
            # We have a winner!!!             
            
                              
    def _is_figure(self, paragraph: str) -> bool:
        return bool(self.re_figure.match(paragraph)) 
                              
    def _is_below_minimum_word_count(self, paragraph: str) -> bool:
        return len(paragraph.split()) < self.MINIMUM_WORD_COUNT 
                              
    def _detect_taxon_names(self, paragraph: str) -> list[Span]:                              
        doc = self.nlp(paragraph)                    
        return [ent for ent in doc.ents if ent.label_ == 'LIVB' and self._is_well_formed_name(ent.text)]   
               
    @staticmethod
    def _is_well_formed_name(taxon_name) -> bool:
        # If a taxa is all upper case (model has misidentified an acronym) or doesn't start with a capital
        return taxon_name[0].isupper() and not taxon_name.isupper()
    
    @staticmethod
    def _get_matching_taxon_names(re_taxon_name: re.Pattern, taxon_names: list) -> list[str]:
        return [name for name in taxon_names if re_taxon_name.search(name)]
        
    @staticmethod
    def _classify_paragraph_is_description(paragraph: str) -> bool:
        return predict(paragraph)  