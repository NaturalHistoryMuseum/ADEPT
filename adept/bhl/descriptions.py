import re
from taxonerd import TaxoNERD
import re
from spacy.tokens import Doc
from spacy.tokens import Span

from adept.bhl.preprocess import BHLPreprocess
from adept.worldflora import WorldFlora
from adept.bhl.classifier import BHLClassifier
from adept.config import logger

Span.set_extension("matched_name", default=None, force=True)

class BHLDetectDescriptions():
    
    # Match 15a. etc., at start of string
    re_figure=re.compile('^[0-9]+[a-zA-Z][.|\s]') 
    re_lower_chars = re.compile('[a-z]+')
     
    wf = WorldFlora()
    taxonerd = TaxoNERD(prefer_gpu=False)
    nlp = taxonerd.load(model="en_ner_eco_biobert", exclude=["pysbd_sentencizer"])    
    preprocess = BHLPreprocess()
    
    classifier = BHLClassifier()
    
    MINIMUM_WORD_COUNT = 50
    
    def __init__(self, taxon: str):
        names = set([taxon])
        if synonyms := self.wf.get_related_names(taxon):
            names |= synonyms        

        logger.debug('Using name and synonyms %s for taxon %s', names, taxon)
        # Add pattern Genus species => G. species

        self.name_map = {
            r'{0}. {1}'.format(n[0][0],n[1]):name for name in names if (n := name.split())
        }      

        try:
            names |= set(self.name_map.keys())
        except IndexError:
            pass         

        self._re_names = self._name_match_regex(names)

    def _name_match_regex(self, names: set):
        names = {n.replace('**', '') for n in names}
        names_pattern = "|".join(re.escape(name) for name in sorted(names, key=len, reverse=True))
        return re.compile(fr'{names_pattern}', re.IGNORECASE)
        
    def __call__(self, text: str):
        text = self.preprocess(text)
        doc = self.nlp(text)  
        doc.ents = self._segment_ents(doc)        
        return self._get_descriptions(doc)
        
    def _get_descriptions(self, doc):
        
        doc_matching_ents = [e for e in doc.ents if e.label_ == 'MATCHING_LIVB']
        seen_matches = []

        # If there's no matching taxa ents
        if not doc_matching_ents:
            return
    
        is_name_match = False

        descriptions = []
        matched_names = set()

        for para in self._doc_to_paragraphs(doc):
            
            if self._is_figure(para.text):
                # logging.debug(f"IS FIGURE: {paragraph}")
                continue     
            
            # If this is a title .e.g. FAMILY~73.. CAPRIFOLIACEAE. BHL 28698273
            # Set name match to none so paras in a new sections aren't included
            if self._is_title(para.text):
                is_name_match = False
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

            # Clean the text prior to running the description classifier
            # Better classification accuracy if we remove the taxon name
            # and any non char prefix/suffix
            clean_text = self._clean_text(para.text, para_matching_ents)

            if not self.classifier.is_description(clean_text):
                continue

            logger.debug(f"Description found for %s", para_matching_ents)  

            matched_names.update({ent._.matched_name for ent in para_matching_ents})

            descriptions.append(para.text)

        if descriptions:
            return descriptions, matched_names
            
    @staticmethod
    def _clean_text(text: str, para_matching_ents:list[Span]) -> str:
        pattern = "|".join(re.escape(ent.text) for ent in para_matching_ents)
        clean_text = re.sub(pattern, "", text)  
        # Remove any non alpha chars at the beginging and end of the text
        # EG 4. ; /. with a lanceolate outline bipinnatifid woolly
        clean_text = re.sub(r'^[^A-Za-z]+|[^A-Za-z]+$', '', clean_text)
        return clean_text        
            
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
        # BUGFIX: remove is acronym check - otherwise not picking up
        # If a taxa is all upper case (model has misidentified an acronym) or doesn't start with a capital
        return taxon_name[0].isupper()
    
    def _is_figure(self, paragraph: str) -> bool:
        return bool(self.re_figure.match(paragraph))  
    
    def _is_title(self, paragraph: str) -> bool:
        if len(paragraph) > 1:
            lower_chars = self.re_lower_chars.findall(paragraph)
            return len(lower_chars) <= 1
    
    def _segment_ents(self, doc: Doc):
        def _get_labelled_ent(ent):
            match = self._re_names.search(ent.text)
            label = "MATCHING_LIVB" if match else "LIVB"            
            # label = 'MATCHING_LIVB' if self._re_names.search(ent.text) else 'LIVB'
            span = Span(ent.doc, ent.start, ent.end, label=label)
            if match:
                name = match.group()                
                span._.matched_name = self.name_map.get(name, name)
            return span
    
        return [_get_labelled_ent(ent) for ent in doc.ents if ent.label_ == 'LIVB' and self._is_well_formed_name(ent.text)]         