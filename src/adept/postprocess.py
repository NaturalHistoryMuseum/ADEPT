from spacy.tokens import Span, Doc

from adept.traits import Traits
from adept.fields import Fields
from adept.utils.helpers import token_get_ent

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
            self._process_colours_fields(sent, fields, part)
            self._process_discrete_fields(sent, fields, part, taxon_group)
            self._process_custom_fields(sent, fields)
            if part:
                self._process_measurement_fields(sent, fields, part)
            self._process_numeric_fields(sent, fields)
                
        return fields
          
    @staticmethod
    def _sent_get_part(sent):
        return sent._.anatomical_part if sent._.anatomical_part else None
    
    def _process_colours_fields(self, sent: Doc, fields: Fields, part: str):
        colour_ents = [ent for ent in sent.ents if ent.label_ == 'COLOUR']
        for ent in colour_ents:
            fields.upsert(f'{part}_colour', 'discrete', ent.lemma_)
            
    def _process_discrete_fields(self, sent: Doc, fields: Fields, part: str, taxon_group: str):
        
        df = self.traits.get_discrete_traits(taxon_group)
        
        trait_ents = [ent for ent in sent.ents if ent.label_ == 'TRAIT']
        # Process entities     
        for ent in trait_ents:                
            mask = ((df.term == ent.lemma_) | (df.term == ent.text))
            # If the trait ent is a part, no need to filter on part         
            if part != ent.lemma_:
                # Plant part is an artificial construct, so we treate it as sent having no part             
                if part and part != 'plant':
                    mask &= (df.part == part)
                # If sent has no part, trait must have no part and must be unique             
                else:
                    mask &= ((df.part.isna()) & (df.unique == True))
                
            rows = df[mask]     
                            
            for row in rows.itertuples():   
                fields.upsert(row.trait, 'discrete', row.character)   
                
    def _process_custom_fields(self, sent: Doc, fields: Fields):         
        for ent in sent.ents:
            if trait_value := ent._.get("trait_value"):
                fields.upsert(ent.label_.lower(), 'discrete', trait_value)        
        

    def _process_measurement_fields(self, sent: Doc, fields: Fields, part: str):
        if sent._.dimensions:     
            field_name = f'{part}_measurement'
            fields.upsert(field_name, 'dimension', sent._.dimensions[0])
        elif sent._.measurements:            
            field_name = f'{part}_measurement'
            fields.upsert(field_name, 'measurement', sent._.measurements)
        elif sent._.volume_measurements:
            field_name = f'{part}_volume'
            fields.upsert(field_name, 'volume', sent._.volume_measurements[0])
            
            
    def _process_numeric_fields(self, sent: Doc, fields: Fields):
        
        # Process numeric values (those not measurements or dimensions)     
        numeric_ents = [ent for ent in sent.ents if ent.label_ in ['CARDINAL', 'QUANTITY'] and not (ent[0]._.is_measurement or ent[0]._.is_dimension)]

        # We use the dependency parse to find nummod noun, that's also an entity     
        for num_ent in numeric_ents:
            root = num_ent.root
            if root.dep_ == 'nummod' and root.head.pos_ == 'NOUN':
                if ent:= token_get_ent(root.head, ['PART', 'TRAIT']): 
                    field_name = ent._.get("anatomical_part") or ent.lemma_
                    fields.upsert(f'{field_name}_number', 'numeric', num_ent)