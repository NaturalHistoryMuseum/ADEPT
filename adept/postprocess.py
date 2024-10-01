from spacy.tokens import Span, Doc

from adept.traits import Traits
from adept.fields import Fields
from adept.utils.helpers import token_get_ent
from adept.config import logger

class Postproccess():
    
    """
    
    Run through the description Doc, parsing the different entities

    Returns:
        _type_: _description_
    """
    
    traits = Traits()
    
    def __call__(self, doc, taxon_group):

        fields = Fields()
        for sent in doc.sents:
            part = self._sent_get_part(sent)            
            self._process_discrete_fields(sent, fields, part, taxon_group)
            self._process_custom_fields(sent, fields)
            if part:
                self._process_measurement_fields(sent, fields, part)
                self._process_colours_fields(sent, fields, part)
            self._process_numeric_fields(doc, sent, fields)
             
        logger.debug(fields.to_dict())   

        return fields
          
    @staticmethod
    def _sent_get_part(sent):
        return sent._.anatomical_part if sent._.anatomical_part else None
    
    def _process_colours_fields(self, sent: Doc, fields: Fields, part: str):
        colour_ents = self._filter_ents(sent, ['COLOUR'])
        for ent in colour_ents:
            fields.upsert(f'{part} colour', 'discrete', ent.lemma_)
            
    def _process_discrete_fields(self, sent: Doc, fields: Fields, part: str, taxon_group: str):        
        df = self.traits.get_discrete_traits(taxon_group)                
        trait_ents = self._filter_ents(sent, ['TRAIT'])
        # Process entities     
        for ent in trait_ents:     
            
            # Special handling for bloody fig.XXX
            if ent.lemma_ == 'fig':
                try: 
                    next_token = ent.doc[ent.end]
                except IndexError:
                    pass
                else:
                    if next_token.text == '.': continue
                                      
            # Match on either term or character 
            mask = (((df.term == ent.lemma_) | (df.term == ent.text.lower()) | (df.character == ent.lemma_) | (df.character == ent.text.lower())))
            # If the trait ent is a part, no need to filter on part        
            if not ent._.anatomical_part:
                if part == 'plant':
                    mask &= ((df.part == part) | (df.part.isna()))
                elif part:
                    mask &= (df.part == part)
                else:
                    mask &= (df.part.isna())
      
            rows = df[mask]    

            for row in rows.itertuples():   
                
                # if row.character == 'syconium':
                #     print('---')
                #     print(row.trait)
                #     print(row)
                #     print(ent)
                #     print(sent)
                                  
                fields.upsert(row.trait, 'discrete', row.character)   
                
    def _process_custom_fields(self, sent: Doc, fields: Fields):         
        for ent in sent.ents:
            if trait_value := ent._.get("trait_value"):
                fields.upsert(ent.label_.lower(), 'discrete', trait_value)        
    
    @staticmethod    
    def _get_sentence_measurements_filtered_by_part(sent, part: str):
        """
        Get sentence measurements, filtering for multiple parts in the sentence
        """
        measurements = [ent for ent in sent.ents if ent.label_ in ['DIMENSION', 'MEASUREMENT']]
        extra_sent_parts = [ent for ent in sent.ents if ent._.anatomical_part and ent._.anatomical_part != part]
        
        # If we have multiple parts and measurements in a sentence, filter the 
        # measurements to only those that proceed the first non-sentence part
        # e.g. Petals 2-3 cm. long and 1-2 mm wide with lamina 2 cm. => Petals 2-3 cm. long and 1-2 mm wide   
        if len(measurements) > 1 and extra_sent_parts:
            # Measurements whose ancestor includes extra sent parts
            # Petals 2-3 cm. long and 1-2 mm wide with 2 cm long lamina => 2cm
            measurements_with_ancestor_parts = [ent for ent in measurements if any(
                [token_get_ent(tok, 'PART') in extra_sent_parts for tok in ent.root.ancestors]
            )]                
            # We only want to use measurements which start before         
            max_start = min([p.start for p in extra_sent_parts + measurements_with_ancestor_parts])
            measurements = [ent for ent in measurements if ent.start < max_start]
            
        return measurements
        
    def _process_measurement_fields(self, sent: Doc, fields: Fields, part: str):
        for ent in self._get_sentence_measurements_filtered_by_part(sent, part):
            field_name = f'{part} measurement'         
            fields.upsert(field_name, 'measurement', ent)               

    @staticmethod
    def _parse_cardinal_part_subject(doc: Doc, cardinal_ent: Span): 
        """
        Use the dependency parse to locate the part/trait subject of a cardinal
        """         
        ent_labels = ['PART', 'TRAIT']
        # The root token of the cardinal ent - will contain the ancestral dependency
        token = cardinal_ent.root
        # If token is a numeric modifier, noun subject is the token head      
        if token.dep_ in 'nummod':
            if subject := token_get_ent(token.head, ent_labels):
                return subject

        # Try and locate a part/trait in the cardinal subtree     
        subtree = doc[token.left_edge.i: token.right_edge.i]
        part_ents = [ent for ent in subtree.ents if ent.label_ in ent_labels]
        if len(part_ents) == 1:
            return part_ents[0]
            
    def _process_numeric_fields(self, doc: Doc, sent: Doc, fields: Fields):        
        # Process numeric values (those not measurements or dimensions)     
        cardinal_ents = self._filter_ents(sent, ['CARDINAL'])       
        for cardinal_ent in cardinal_ents:
            if ent := self._parse_cardinal_part_subject(doc, cardinal_ent):  
                field_name = ent._.get("anatomical_part") or ent.lemma_
                fields.upsert(f'{field_name} number', 'numeric', cardinal_ent)
                
    @staticmethod
    def _filter_ents(sent: Span, label: list):
        return [ent for ent in sent.ents if ent.label_ in label]