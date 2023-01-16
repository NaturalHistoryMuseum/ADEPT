import csv
import spacy
import re
import enum
from fractions import Fraction

from spacy.language import Language
from spacy.tokens import Doc
from spacy.matcher import Matcher
from spacy.tokens import Span, Token
from spacy import displacy
from spacy.util import filter_spans


from adept.components.base import BaseComponent
from adept.utils.expand import ExpandSpan




class NumericExpand(BaseComponent):
    
    """

    Correct the CARDINAL & QUANTITY entities - expanded to their full value
    
    Sets an extension _is_modified_numeric on the sent span, so can
    Be used in script numeric.py to build a train dataset
    
    """
    
    
    name = "numeric_expand"

    # Needs to come after the NER
    pipeline_config = {'after': 'ner'}  
    
    def __init__(self, nlp):                 

        super().__init__(nlp)
        self.matcher = Matcher(nlp.vocab)   
        self.matcher.add('NUMERIC', [[{"POS": "NUM"}]])
    
        self.expand_numeric = ExpandSpan(
            ['-', '(', ')', '+', 'cm', 'mm', 'm', '×', 'x'], 
            pos_tags=['NUM'],
            entity_types=['QUANTITY', 'CARDINAL']
        )
                
        Span.set_extension("is_expanded_numeric", default=None, force=True)      
    
        
    def __call__(self, doc):
        
        orig_ents = set(doc.ents)
        ents = set()
        
        for _, start, end in self.matcher(doc): 

            token = doc[start]                                       
            span = self.expand_numeric(doc, token)            
            has_unit = [t for t in span if t.lower_ in ['mm', 'cm', 'm']]            
            label = 'QUANTITY' if has_unit else 'CARDINAL'
            ent = Span(doc, span.start, span.end, label=label)

            ents.add(ent) 
            
        # Get all the new ents       
        new_ents = ents.difference(orig_ents)
                  
        doc.ents = set(filter_spans(new_ents | orig_ents)) 
        
        for ent in new_ents:
            ent.sent._.is_expanded_numeric = True
        
        return doc
            


if __name__ == '__main__':
    
    nlp = spacy.load("en_core_web_trf")

    ner = NumericExpand(nlp)

    # text = 'A glabrous perennial 15-30(-40) cm. Rhizomes far-creeping producing tufts of 1-3 shoots at ± regular intervals. Roots pale yellow-brown. Scales grey brown, often tinged wine red, soon becoming fibrous.           Stems trigonous, smooth below, rough above, ± decumbent at base. Lvs 12-40 x 2-4 mm, concave, often curved, thick, bluntly keeled or channelled, gradually tapering to a trigonous point up to 5 cm long, mid green, ± shiny. Ligule 1-4 mm, broadly ovate or almost truncate. Lower sheaths lfless, persistent, thick, white, tinged with red. Infl 1/5-1/4 lngth of stem. Lower bract lf-like, about as long as infl, not sheathing, upper glumaceous.  Male spike 1(-2), 10-15 x 3 mm, fusiform. Male glumes 3-4 mm, ovate, acute or obtuse, dark purple-black with hyaline margin. Female spikes 1-2(-3), ± contiguous, (5-)10-15(-20) x 4-5 mm, ovoid or subglobose, erect, lower peduncled, upper ±  sessile. Female glumes 2-3 mm, ovate, acute, dark purplish-brown with pale midrib and hyaline margin, shorter than fr.  Utricle 3-3.5 mm, smooth, ±          inflated, dark purple green in upper half, shiny. Beak 0.5 mm, ± notched. Stigmas 2, rarely 3. Nut 2 mm, subglobose.'
    text = 'Plants perennial; rhizomatous or stoloniferous, rhizomes or stolons to 5 cm. Culms 10-75 cm, erect or geniculate, with 2-5 nodes. Leaves basal and cauline; sheaths smooth; ligules 0.3-2 mm, shorter than wide, dorsal surfaces usually scabridulous, sometimes smooth, apices truncate to rounded, erose-ciliolate, sometimes lacerate; blades 3-10 cm long, 1-5 mm wide, flat. Panicles 3-20 cm long, less than 1/2 the length of the culm, (1)2-12 cm wide, stiffly erect, widely ovate, open, exserted from the upper sheaths at maturity, lowest node with (2)3-9(13) branches; branches smooth or scabridulous, spreading during and after anthesis, spikelets usually confined to the distal 1/2, lower branches 1.5-7 cm; pedicels 0.4-3.3 mm, adjacent pedicels divergent. Spikelets lanceolate or oblong, purplish brown to greenish. Glumes subequal, 1.7-3 mm, 1-veined, acute; lower glumes scabridulous over the midvein towards the apices; upper glumes scabridulous or smooth over the midvein; calluses glabrous, or with a few hairs to 0.1 mm; lemmas 1.2-2.5 mm, smooth, glabrous, opaque to translucent, 3(5)-veined, veins typically prominent, apices obtuse to acute, usually entire, sometimes the veins excurrent to 0.5 mm, usually unawned, rarely awned, sometimes varying within a panicle, awns to 2 mm, mid-dorsal, straight or geniculate; paleas 0.6-1.2(1.4) mm, typically at least 1/2 the length of the lemmas, veins visible; anthers 3, 0.8-1.3 mm. Caryopses 0.8-1.5 mm; endosperm solid. 2n = 28.'

    doc = nlp(text)

    doc = ner(doc)  
    
    for ent in doc.ents:
        print(ent)
        print(ent.label_)    


