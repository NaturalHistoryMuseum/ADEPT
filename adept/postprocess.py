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
            self._process_numeric_fields(doc, sent, fields)
                
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
            mask = (((df.term == ent.lemma_) | (df.term == ent.text)) | ((df.character == ent.lemma_) | (df.character == ent.text)))
            
            no_part_submask = ((df.part.isna()) & (df.is_unique == True))
            no_part_required_submask = ((df.require_part == False) & (df.is_unique == True))
            
            # If the trait ent is a part, no need to filter on part         
            if part != ent.lemma_:
                if part and part != 'plant':
                    mask &= ((df.part == part) | no_part_submask | no_part_required_submask )
                else:
                    mask &= no_part_submask | no_part_required_submask
                                     
            rows = df[mask]    

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
    
    @staticmethod
    def _parse_cardinal_part_subject(doc: Doc, cardinal_ent: Span): 
        """
        Use the dependency parse to locate the part/trait subject of a cardinal
        """         
        ent_labels = ['PART', 'TRAIT']
        # The root token of the cardinal ent - will contain the ancestral dependency
        token = cardinal_ent.root
        # If token is a numeric modifier, noun subject is the token head      
        if token.dep_ == 'nummod':
            return token_get_ent(token.head, ent_labels)

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