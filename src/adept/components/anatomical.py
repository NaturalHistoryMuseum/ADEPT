import csv

import spacy
from spacy.language import Language
from spacy.tokens import Doc
from spacy.matcher import Matcher
from spacy.tokens import Span, Token
from spacy import displacy
from spacy.pipeline import EntityRuler
from pathlib import Path
from itertools import chain
import yaml

from adept.components.base import BaseComponent
from adept.tasks.patterns.anatomy import AnatomyPatternsTask, AnatomicalPartsTask



class AnatomicalEntity(EntityRuler, BaseComponent):
    
    name = 'anatomical_entity'
    
    # We want this to run before the main NER, so it will 
    pipeline_config = {'before': 'ner'}        
    patterns_file_path = AnatomyPatternsTask().output().path
    anatomical_parts_file_path = Path(AnatomicalPartsTask().output().path)
    
    def __init__(self, nlp, *args, **cfg):
        super().__init__(nlp, overwrite_ents=True, *args, **cfg)
        
        self.from_disk(self.patterns_file_path)        
        Span.set_extension("anatomical_part", default=None, force=True)
        
        with self.anatomical_parts_file_path.open() as f:        
            anatomical_parts = yaml.full_load(f)
            # Dict of part synonyms, so when we set the part we use the term, not the synonym
            # e.g. {leaves => leaf}
            self.part_synonyms = dict(chain(*[[(syn, part) for syn in syns] for part, syns in anatomical_parts.items() if syns]))

    def set_annotations(self, doc, matches):
        # Super to sent the ents    
        super().set_annotations(doc, matches)
        
        for match_id, start, end in matches:
            span = doc[start:end]     
            part = span.lemma_.lower()
            # Set part to the term, not the synonym
            if part in self.part_synonyms:
                part = self.part_synonyms[part]  
             
            # Set the anatomical_part to the root (non-synonym) part term
            span._.anatomical_part = part

        # But we also want to set the anatomical_part of the sent
        # By identifying which ent is the sent subject
        for i, sent in enumerate(doc.sents):
            if i == 0: sent._.anatomical_part = 'plant'
            if subject_part := self._sent_get_subject_part(sent):
                sent._.anatomical_part = subject_part._.anatomical_part
                                        
    def _sent_get_subject_part(self, sent):
        parts = [e for e in sent.ents if e.label_ == 'PART']

        if not parts:
            return   
        
        subject_part = self._sent_get_noun_subject_part(parts)  
        
        if not subject_part:
            first_part = parts[0]
            # Is the first part the first sentence, then use it as a subject        
            if first_part.start == sent.start:
                subject_part = parts[0]
            # Or if the first part is the second word, preceeded by a modifier         
            # For example: lower bract         
            elif first_part.start == sent.start + 1 and sent[0].dep_ == 'amod':
                subject_part = parts[0]        
                
        return subject_part       
        
    @staticmethod        
    def _sent_get_noun_subject_part(parts):
        
        def token_is_subject_noun(token):
            return token.dep_ == "nsubj" or (token.dep_ == "ROOT" and token.pos_ == "NOUN")
    
        for part in parts:
            if any([t for t in part if token_is_subject_noun(t)]):
                return part

if __name__ == '__main__':

    nlp = spacy.load("en_core_web_trf")

    ner = AnatomicalEntity(nlp)

    # text = 'A glabrous perennial 15-30(-40) cm. Rhizomes far-creeping producing tufts of 1-3 shoots at ± regular intervals. Roots pale yellow-brown. Scales grey brown, often tinged wine red, soon becoming fibrous.           Stems trigonous, smooth below, rough above, ± decumbent at base. Lvs 12-40 x 2-4 mm, concave, often curved, thick, bluntly keeled or channelled, gradually tapering to a trigonous point up to 5 cm long, mid green, ± shiny. Ligule 1-4 mm, broadly ovate or almost truncate. Lower sheaths lfless, persistent, thick, white, tinged with red. Infl 1/5-1/4 lngth of stem. Lower bract lf-like, about as long as infl, not sheathing, upper glumaceous.  Male spike 1(-2), 10-15 x 3 mm, fusiform. Male glumes 3-4 mm, ovate, acute or obtuse, dark purple-black with hyaline margin. Female spikes 1-2(-3), ± contiguous, (5-)10-15(-20) x 4-5 mm, ovoid or subglobose, erect, lower peduncled, upper ±  sessile. Female glumes 2-3 mm, ovate, acute, dark purplish-brown with pale midrib and hyaline margin, shorter than fr.  Utricle 3-3.5 mm, smooth, ±          inflated, dark purple green in upper half, shiny. Beak 0.5 mm, ±          notched. Stigmas 2, rarely 3. Nut 2 mm, subglobose.' 
    text = "Perennials, 40-100 cm tall 1 x 2 cm (usually rhizomatous, sometimes stoloniferous). Stems 1(-4), erect, simple or branched, densely lanate-tomentose to glabrate. Leaves petiolate (proximally) or sessile (distally, weakly clasping and gradually reduced); blades oblong or lanceolate, 3.5-35+ cm x 5-35 mm, 1-2-pinnately lobed (ultimate lobes +- lanceolate, often arrayed in multiple planes), faces glabrate to sparsely tomentose or densely lanate. Heads 10-100+, in simple or compound, corymbiform arrays. Phyllaries 20-30 in +- 3 series, (light green, midribs dark green to yellowish, margins green to light or dark brown) ovate to lanceolate, abaxial faces tomentose. Receptacles convex; paleae lanceolate, 1.5-4 mm. Ray florets (3-)5-8, pistillate, fertile; corollas white or light pink to deep purple, laminae 1.5-3 x 1.5-3 mm. Disc florets 10-20; corollas white to grayish white, 2-4.5 mm. Cypselae 1-2 mm (margins broadly winged). 2n = 18, 27, 36, 45, 54, 63, 72 (including counts from Europe). Morphologic characters that have been used to segregate these populations into species and/or varieties include: (1) degree and persistence of tomentum; (2) phyllaries with greenish, light brown, or dark brown margins; (3) shapes of capitulescences (rounded or flat-topped); and (4) degrees of leaf dissection and shapes of lobes."
    
    
    doc = nlp(text)

    doc = ner(doc)
    
    for sent in doc.sents:
        print(sent._.anatomical_part)
    
    # for ent in doc.ents:
    #     print(ent.label_, ent.text)