from abc import ABC, abstractmethod
from collections import OrderedDict
from pathlib import Path
from spacy.tokens import Span, Doc
import re
import yaml

from adept.config import unit_registry, logger, DimensionType, DEFAULT_MEASUREMENT_UNIT
from adept.utils.helpers import flatten_dict

class Field(ABC):
    
    unique = False
    
    def __init__(self, name):
        self.name = name
        self.value = set()

    @property
    @abstractmethod
    def field_type(self):
        pass        
        
    def set_value(self, value):
        self.value.add(value)
    
    def get_value(self):
        return ', '.join(self.value)
    
    def __repr__(self):
        return f'{self.__class__.__name__}({self.value})'
    
class NumericField(Field):
    
    num_re = re.compile(r'(\d+(?:\.\d+)?)')
    field_type = 'numeric'
    
    def set_value(self, ent: Span):
        self.value = self._get_ent_value(ent)
        
    def get_value(self):
        if self.value:
            return {k: str(v) for k, v in self.value.items()}
    
    def _get_ent_value(self, ent: Span) -> dict:
        if ent._.numeric_range:
            value = ent._.numeric_range
        elif ent._.numeric_value:
            value = {'from': ent._.numeric_value, 'to': ent._.numeric_value} 
        else:
            return {}               
        return self._to_min_max(value)


    def _to_min_max(self, value_dict):
        unpack = lambda ks: ([v for k in ks if (v := value_dict.get(k))])
        return {
            'min': min(unpack(['lower', 'from']), default=None),
            'max': max(unpack(['to', 'upper']), default=None)
        }  

class MeasurementField(NumericField):
    
    field_type = 'measurement'
    
    def __init__(self, name):
        self.name = name
        self.value = {}
 
    # In botanical descriptions length measurements are provided first, then width.  
    # These can be set without specifying a dimension_type
    implicit_dimension_types = [DimensionType.LENGTH, DimensionType.WIDTH]
    
    def set_value(self, ent):
        if dimension_ents := ent._.get("dimension_parts"):      
            for dimension_type, ent in zip(self.implicit_dimension_types, dimension_ents):        
                self._set_value(ent, dimension_type)
        else:
            dimension_type = DimensionType[ent._.measurement_dimension.label_] if ent._.measurement_dimension else None
            try:
                dimension_type = self.validate_dimension_type(dimension_type)
            except Exception as e:
                logger.error(e)
                return            
            self._set_value(ent, dimension_type)
        
    def validate_dimension_type(self, dimension_type : DimensionType = None):
        existing_dimension_types = list(self.value.keys())
        if dimension_type: 
            
            if dimension_type in existing_dimension_types:
                raise Exception(f'Field {self.name} already has a value for {dimension_type}')
            
            return dimension_type
        
        if self.value:  # No dimension type specfied, and we already have a value
            # if the existing existing_dimension_type is first entry in list ([DimensionType.LENGTH]),
            # dimension type will be second implicit value - DimensionType.WIDTH
            if existing_dimension_types != self.implicit_dimension_types[:1]:
                raise Exception(f'Field {self.name} already has values for {[t.name for t in existing_dimension_types]} and no dimension type specified')
            
            return self.implicit_dimension_types[1]
                                  
        # No dimension type specified, and no existing value
        return self.implicit_dimension_types[0]        
        
    def get_value(self, target_unit=None):
        data = {}   
        for dimension_type, value_dict in self.value.items():
            data[dimension_type.name.lower()] = {k: self._format_output(v, target_unit) for k, v in value_dict.items() if v}
        return data
    
    def _format_output(self, value, target_unit=None):
        if target_unit:
            value = value.to(target_unit)

        # Convert value to string - uses the default formatting set in adept.config unit_registry.default_format  
        return f'{value}'

    def _set_value(self, ent, dimension_type):                  
        unit = ent._.unit        
        # Some measurements are detected, but have no unit. 
        # E.g. Petals white, suborbicular, 6-7 x 5-6.
        # No unit = do not use the measurement                
        if not unit:
            logger.error('Measurement field %s: No unit detected - %s', self.name, ent.text)
            return
                  
        if value_dict := self._get_ent_value(ent):
            value_dict = {x: self._to_unit(y, unit) for x, y in value_dict.items() if y}
            self.value[dimension_type] = value_dict        
        
    def _to_unit(self, value, unit):
        if value:
            return value * unit
         
            
class DiscreteField(Field):
    
    field_type = 'discrete'
 
class Fields(object):
    
    _classes = {
        fld_cls.field_type: fld_cls for fld_cls in [DiscreteField, MeasurementField, NumericField]
    }
    re_unit = re.compile('\[([a-z³]+)\]')
    
    def __init__(self):
        self._fields = OrderedDict()
        
    def upsert(self, field_name, field_type, value):
        # If we do not already have the field defined create it       
        if not field_name in self._fields: 
            self._fields[field_name] = self._factory(field_type, field_name)
            
        self._fields[field_name].set_value(value)
            
    def _factory(self, field_type, field_name):
        return self._classes[field_type](field_name)  
    
    def to_dict(self, field_configs={}):
        data = OrderedDict()
        for field in self._fields.values():
            field_config = field_configs.get(field.name, {})
            if field.field_type == MeasurementField.field_type and not field_config.get('target_unit'):
                field_config['target_unit'] = DEFAULT_MEASUREMENT_UNIT                
            if value := field.get_value(**field_config): 
                value_dict = {field.name: value}
                if isinstance(value, dict):
                    # We want to turn measurement dicts etc into single dimension dicts e.g.
                    # {'field_name': {'y': {'min': 40.0, 'max': 100.0}}} => {'field_name.y.min': 40.0, 'field_name.y.max': 100.0}
                    value_dict = flatten_dict(value_dict)
                data.update(value_dict)                   
        return data   
    
    def build_fields_config(self,field_mappings: dict):
        """
        Build field configs based on template name - pull out measurement unit
        """
        field_configs = {}
        for template_name, field_name in field_mappings.items():
            if unit := self.extract_unit(template_name):
                # Some field names cna be a list, so ensure all are a list
                field_name_list = field_name if isinstance(field_name, list) else [field_name]
                for fn in field_name_list:
                    # We just want the first part of the field name seed measurement.y.max => seed measurement
                    fn_part = fn.split('.')[0]
                    field_configs[fn_part] = {'target_unit': unit}
                    
        return field_configs
    
    def to_mapped_dict(self, field_mappings):   
        
        field_configs = self.build_fields_config(field_mappings)
        data_dict = self.to_dict(field_configs)
        
        def _get_value(field_name):
            field_names = field_name if isinstance(field_name, list) else [field_name] 
            for field_name in field_names:
                if value := data_dict.get(field_name):
                    return value
        
        return OrderedDict([(template_name, _get_value(field_name or template_name)) for template_name, field_name in field_mappings.items()])

    def extract_unit(self, string):        
        if match := self.re_unit.search(string):
            return match.group(1)