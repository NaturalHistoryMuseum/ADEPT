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
            self._process_discrete_fields(sent, fields, part, taxon_group)
            self._process_custom_fields(sent, fields)
            if part:
                self._process_measurement_fields(sent, fields, part)
                self._process_colours_fields(sent, fields, part)
            self._process_numeric_fields(sent, fields)
                
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
      
            # Match on either term or character 
            mask = (((df.term == ent.lemma_) | (df.term == ent.text)))
            
            # If the trait ent is a part, no need to filter on part         
            if part != ent.lemma_:

                # If we have part, allow traits with matching part
                if part and part != 'plant':
                    mask &= (df.part == part)
                
                # For all, allow where no part and unique
                mask |= ((df.part.isna()) & (df.is_unique == True))
            
            # if part and part != 'plant':
            #     # If we have a part, filter on part or unique
            #     # Plant part is an artificial construct, so we treate it as sent having no part
            #     mask &= ((df.part == part) | (df.is_multiple == False))
            # else:
            #     # If sent has no part, trait must have no part and must not be multiple
            #     mask &= ((df.part.isna()) & (df.is_multiple == False))
            
            #          
            # if part != ent.lemma_:
            #     print('NOPE')
            #     print(part)
            #     # Plant part is an artificial construct, so we treate it as sent having no part             
            #     if part and part != 'plant':
            #         mask &= (df.part == part)
            #     # If sent has no part, trait must have no part and must be unique             
            #     else:
            #         mask &= ((df.part.isna()) & (df.unique == True))
                
                        
                
            rows = df[mask]     
            
            # print(ent)
            # print(rows)
     
            for row in rows.itertuples():   
                fields.upsert(row.trait, 'discrete', row.character)   
                
    def _process_custom_fields(self, sent: Doc, fields: Fields):         
        for ent in sent.ents:
            if trait_value := ent._.get("trait_value"):
                fields.upsert(ent.label_.lower(), 'discrete', trait_value)        
        

    def _process_measurement_fields(self, sent: Doc, fields: Fields, part: str):
        ents = self._filter_ents(sent, ['MEASUREMENT', 'DIMENSION', 'VOLUME'])
        for ent in ents:
            field_type = ent.label_.lower()
            if ent.label_ == 'VOLUME':
                field_name = f'{part} volume'
            else:
                field_name = f'{part} measurement'

            fields.upsert(field_name, field_type, ent)            
            
    def _process_numeric_fields(self, sent: Doc, fields: Fields):        
        # Process numeric values (those not measurements or dimensions)     
        cardinal_ents = self._filter_ents(sent, ['CARDINAL'])       
        # We use the dependency parse. If cardinal is a numeric modifier of a noun
        # If dep_nummod noun, if the noun is a part or trait, set the value     
        for cardinal_ent in cardinal_ents:
            # The root token of the carinal ent - the one that will contain the ancestral dependency 
            token = cardinal_ent.root
            if token.dep_ == 'nummod':
                if ent := token_get_ent(token.head, ['PART', 'TRAIT']):            
                    field_name = ent._.get("anatomical_part") or ent.lemma_
                    fields.upsert(f'{field_name} number', 'numeric', cardinal_ent)
                
    @staticmethod
    def _filter_ents(sent: Span, label: list):
        return [ent for ent in sent.ents if ent.label_ in label]