import re
from tokenize import Token
from spacy.matcher import Matcher
from spacy.tokens import Span, Doc
from decimal import Decimal, InvalidOperation

from adept.config import logger, measurement_units, unit_registry


class NumericComponent: 
    
    """
    Loop through MEASUREMENT', 'DIMENSION', 'CARDINAL', 'VOLUME' ents, parsing the value & extracting the unit
    
    If numeric range: sets extension numeric_range with keys: lower, from, to, upper
    If not range, sets float numeric_value
    Dimension ents are split into parts in dimension_parts
    
    
    Returns:
        doc: doc object with extensions: numeric_range, numeric_value, dimension_parts, unit
    """
    
    ent_types = ['MEASUREMENT', 'VOLUME', 'CARDINAL', 'DIMENSION']
    
    # Match digit, and allow a dot, if it's part of at least one digit   
    re_num = re.compile(r'([\d]+[\.]{,1}[\d]*)')
    re_outer = re.compile(r'((?P<lower>[\d.\/\s]+)\-?\))?\s?(?P<inner>[\d\-]+[\s\d\-\.]*)\s?(\(\-?(?P<upper>[\d.\/\s]+))?')    
    # re_outer = re.compile(r'((?P<lower>[\d.\/\s]+)\-?\))?(?P<inner>[\s\-]?[\d][\d\-\s\.]+)\((?P<upper>.+)')
    re_inner = re.compile(r'(?P<from>([\d][\d\.]{0,}))?\s?\-?\s?(?P<to>([\d][\d\.]{0,}))?')
  
    units_pattern = '|'.join([unit for unit in measurement_units])       
    re_units = re.compile(f'([\s0-9])(?P<unit>({units_pattern})+)') # Include + so mm is preferred to m
    # BS Bug fix: add [\s0-9] so the unit is preceeded by digit or space - prevent matching 20 em
    
    def __init__(self, nlp):   
        Span.set_extension("numeric_range", default=[], force=True)
        Span.set_extension("numeric_value", default=[], force=True)
        Span.set_extension("dimension_parts", default=[], force=True)
        Span.set_extension("unit", default=None, force=True)    
    
    def __call__(self, doc): 
                
        ents = [ent for ent in doc.ents if ent.label_ in self.ent_types]        
        
        for ent in ents:
            if ent.label_ == 'DIMENSION':
                self._parse_dimension_ent(ent, doc)
            else:
                self._parse_value(ent)
                
        return doc
                
    def _parse_dimension_ent(self, ent, doc):
        if dimensions := self._split_span_on_x(ent, doc):
            for dimension in dimensions:
                self._parse_value(dimension) 
                
            # If the first dimension unit is not set, it is only set at the end 
            # e.g. 10-20(-40) x (8-)10-30(-35) mm    
            #  So copy it to the first ent
            if not dimensions[0]._.unit: dimensions[0]._.unit = dimensions[1]._.unit  
            ent._.set("dimension_parts", dimensions)

    def _parse_value(self, ent: Span):
        self._parse_unit(ent)
        self._parse_numeric(ent)   
        
    def _parse_unit(self, ent: Span):
        unit_match = self.re_units.search(ent.text)
        if unit_match: 
            ent._.unit = getattr(unit_registry, unit_match.group('unit'))          
            
    def _parse_numeric(self, ent: Span):
        # Extract the numeric parts of the ent text
        # 10 - 20 => [10, 20]
        # If we just try converting the ent.text to Decimal, it will at ca. 10
        num_parts = self.re_num.findall(ent.text)
        if len(num_parts) == 1:
            try:
                ent._.set("numeric_value", Decimal(num_parts[0]))
            except InvalidOperation:
                logger.error('Error parsing numeric value "%s"', ent.text)
                
        elif 1 <= len(num_parts) <= 4:  # More than 4 won't be parsed
            numeric_range = self._parse_numeric_range(ent.text)
            ent._.set("numeric_range", numeric_range)
         
    def _parse_numeric_range(self, string):         
        outer_match = self.re_outer.search(string)
        try:
            match_dict = outer_match.groupdict()
            inner = match_dict.pop('inner')
            # print(match_dict)
            inner_match = self.re_inner.search(inner)
            match_dict.update(inner_match.groupdict())     
            # print(match_dict)
        except AttributeError:
            logger.error('Error parsing range "%s": could not parse groups', string)
            return
                    
        try:
            numeric_range = {k: Decimal(v) for k, v in match_dict.items() if v}
        except InvalidOperation:
            logger.error('Error parsing range "%s": non decimal value', match_dict)
            return
                                
        # Quick validation we've extracted all the parts         
        if len(numeric_range) != len(self.re_num.findall(string)):
            logger.error('Error parsing range "%s": incorrect number of elements', string)
            return
        
        return numeric_range


    @staticmethod
    def _split_span_on_x(ent: Span, doc: Doc):

        if x := next((token for token in ent if token.lower_ in ['x', 'by']), None):
            nbor = x.nbor()
            return [doc[ent.start: x.i], doc[nbor.i: ent.end]]        
            
        logger.error('Could not split dimension "%s" in sentence: %s', ent, ent.sent)  
            

    
    
