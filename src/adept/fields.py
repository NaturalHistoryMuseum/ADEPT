from abc import ABC, abstractmethod
from collections import OrderedDict
from pathlib import Path
from spacy.tokens import Span
import re
import yaml

from adept.config import unit_registry
from adept.utils.helpers import flatten_dict

class Field(ABC):
    
    unique = False
    
    def __init__(self, name):
        self.name = name
        self.value = {} if self.unique else set()
        
    @abstractmethod
    def set_value(self, value):
        pass
    
    def get_value(self):
        return ', '.join(self.value)
    
    def __repr__(self):
        return f'{self.__class__.__name__}({self.value})'

class MeasurementField(Field):
    
    # Length/height measurements are provided first, followed by width. 
    dimension_axes = ['y', 'x']    
    unique = True

    def set_value(self, measurements):        
        if self.value: raise Exception(f'Field {self.name} already has a value')
        self._set_value(measurements)
        
    def get_value(self, axis=None, minmax=None, unit=None):
        if unit:
            unit = unit_registry(unit)
        
        data = {}
        # Build a dict of the values x.min         
        for value_axis, value_dict in self.value.items():
            data.setdefault(value_axis, {})
            for mm, value in value_dict.items():
                if unit:
                    value = self.convert_value(value, unit)
                data[value_axis][mm] = self._to_string(value)

        # If axis / minmax set, filter the data
        # FIXME: If minmax set, and not axis, this will fail
        try:         
            if axis: data = data[axis]
            if minmax: data = data[minmax]
        except KeyError:
            # We can ignore this: measurements that have just length will not contain x axis
            pass
        return data
    
    @staticmethod 
    def _to_string(value):
        # Convert value to string - uses the default formatting set in adept.config unit_registry.default_format  
        return f'{value}'

    @staticmethod 
    def convert_value(value, unit):
        return value.to(unit)
        
    def _set_value(self, measurements):  
        # If we have two measurements, treat them as y, x         
        if len(measurements) == 2:
            for axis, measurement in zip(self.dimension_axes, measurements):
                self._set_axis_value(axis, measurement, measurement._.measurement_unit)
        elif len(measurements) == 1:
            measurement = measurements[0]
            self._set_axis_value(self.dimension_axes[0], measurement, measurement._.measurement_unit)
        
    def _set_axis_value(self, axis, measurement: Span, unit):
        if value := self._get_minmax_value(measurement, unit):
            self.value[axis] = value

    def _get_minmax_value(self, measurement: Span, unit):
        # Some measurements are detected, but have no unit. 
        # E.g. Petals white, suborbicular, 6-7 x 5-6.
        # No unit = do not use the measurement        
        if not unit: return
        value_dict = self._get_ent_value(measurement)
        unpack = lambda ks: ([v for k in ks if (v := value_dict.get(k))])
        return {
            'min': self._to_unit(min(unpack(['lower', 'from']), default=None), unit),
            'max': self._to_unit(max(unpack(['to', 'upper']), default=None), unit)
        }
        
    @staticmethod
    def _to_unit(value, unit):
        if value:
            return float(value) * unit
    
    @staticmethod
    def _get_ent_value(ent: Span):
        if ent._.numeric_range:
            value = ent._.numeric_range
        else:
            # Also validate shape is d, dd, so cast to int won't fail
            num = [int(token.text) for token in ent if token.pos_ == 'NUM' and set(token.shape_) == set('d')]
            value = {'from': min(num, default=None), 'to': max(num, default=None)} 
   
        return value  
      
class DimensionField(MeasurementField):
    
    def _set_value(self, dimension):        
        for i, axis in enumerate(self.dimension_axes):                    
             # 0 => 1; 1 => 0
            adj_i = (i-1)**2
            ent = dimension.ents[i]
            # Sometimes the unit is only attached to one of the dimensions e.g. 1.5-2 x 1.7-2.2 cm             
            unit = ent._.measurement_unit or dimension.ents[adj_i]._.measurement_unit            
            self._set_axis_value(axis, ent, unit)  

class VolumeField(MeasurementField):   
    def _set_value(self, volume):          
        self.value = self._get_minmax_value(volume, volume._.measurement_unit)

    def get_value(self, minmax=None, unit=None):
        if unit:
            unit = unit_registry(unit)        
        data = {}        
        for mm, value in self.value.items():
            if unit:
                value = self.convert_value(value, unit)  
            data[mm] = self._to_string(value)
        if minmax: data = data[minmax]
        return data    
    
            
class DiscreteField(Field):
    def set_value(self, value):
        self.value.add(value)

class NumericField(Field):
    def set_value(self, num_ent: Span):
        self.value = num_ent._.get("numeric_range") or num_ent.text
    def get_value(self):
        return self.value

class FieldOutputTemplate():
    
    """
    Load output field defintions from a template file, and map the output to the field names
    We do this, so th eoutput can be prepared for AC
    """
    
    regexes = {
        'unit': re.compile('\[([a-z³]+)\]'),
        'minmax': re.compile(r'\b(min|max)\b'),
        'axis': re.compile(r'\b(x|y)\b')
    }

    def __init__(self, template_path: Path):
        with template_path.open('r') as f:
            self._tpl = yaml.full_load(f)
        
    def get_data(self, fields):
        return {src: self._get_value(src, targets, fields) for src, targets in self._tpl.items()}
        
    def _get_value(self, src, targets, fields):        
        # Template can have a list of targets - so if just a string convert to a list         
        if not isinstance(targets, list):
            targets = [targets]
            
        for target in targets:
            if value := self._get_field_value(src, target, fields):
                return value
            
    def _get_field_value(self, src, target, fields):        
        field_dict = {}
        self._re('unit', src, field_dict)
        if target:
            field_name = target.split('.')[0]
            self._re('minmax', target, field_dict)
            self._re('axis', target, field_dict)
        else:
            field_name = src

        if field := fields.get(field_name):
            return field.get_value(**field_dict)
            
    def _re(self, name, field_name, field_dict):        
        if match := self.regexes[name].search(field_name):
            field_dict[name] = match.group(1)
        
class Fields(object):
    
    _classes = {
        'discrete': DiscreteField,
        'measurement': MeasurementField,
        'dimension': DimensionField,
        'numeric': NumericField,
        'volume': VolumeField,
    }    
    
    def __init__(self):
        self._fields = OrderedDict()
        
    def upsert(self, field_name, field_type, value):
        # If we do not already have the field defined create it         
        if not field_name in self._fields: 
            self._fields[field_name] = self._factory(field_type, field_name)

        self._fields[field_name].set_value(value)
            
    def _factory(self, field_type, field_name):
        return self._classes[field_type](field_name)  
    
    def to_dict(self):
        data = OrderedDict()
        for field in self._fields.values():    
            value = field.get_value()
            value_dict = {field.name: value}
            if isinstance(value, dict):
                # We want to turn measurement dicts etc into single dimension dicts e.g.
                # {'field_name': {'y': {'min': 40.0, 'max': 100.0}}} => {'field_name.y.min': 40.0, 'field_name.y.max': 100.0}
                value_dict = flatten_dict(value_dict)
            data.update(value_dict)   
        return data   
    
    def to_template(self, template_path: Path):
        tpl = FieldOutputTemplate(template_path)
        return tpl.get_data(self._fields)
        