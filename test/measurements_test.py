import unittest
from spacy.tokens import Doc, Span

from adept.pipeline import Pipeline
from adept.config import RAW_DATA_DIR


class MeasurementsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):    
        cls.pipeline = Pipeline()
        text = "Herbs to 40-100 cm tall.  Leaves 10 cm long and 20 - 50 cm wide. Petals 15 x 20 cm. Spike 10 cm wide and 15 cm. Roots 60 cm deep. Seeds 10-20 mm diameter."
        cls.fields = cls.pipeline(text, 'angiosperm')  
        cls.fields_dict = cls.fields.to_dict()          
        cls.sents = list(cls.pipeline.doc.sents)    

    def _get_ents(self, doc: Doc, ent_type: str):
        return  [ent for ent in doc.ents if ent.label_ == ent_type] 

    def test_measurement_ent(self):   
        sent =self.sents[0]               
        ent = self._get_ents(sent, 'MEASUREMENT')
        self.assertEqual(ent[0].text, '40-100 cm')
        
    def test_plant_min_height(self): 
        self.assertEqual(self.fields_dict['plant measurement.height.min'], '40 cm')

    def test_plant_max_height(self): 
        self.assertEqual(self.fields_dict['plant measurement.height.max'], '100 cm')

    def test_leaf_length(self): 
        self.assertEqual(self.fields_dict['leaf measurement.length.min'], '10 cm')

    def test_leaf_min_width(self): 
        self.assertEqual(self.fields_dict['leaf measurement.width.min'], '20 cm')

    def test_leaf_max_width(self): 
        self.assertEqual(self.fields_dict['leaf measurement.width.max'], '50 cm')

    def test_seed_min_diameter(self): 
        self.assertEqual(self.fields_dict['seed measurement.diameter.min'], '10 mm')

    def test_seed_max_diameter(self): 
        self.assertEqual(self.fields_dict['seed measurement.diameter.min'], '10 mm')

    def test_spike_width(self): 
        self.assertEqual(self.fields_dict['spike measurement.width.min'], '10 cm')

    def test_spike_length(self): 
        self.assertIsNone(self.fields_dict.get('spike measurement.length.min'))

    def test_root_depth(self): 
        self.assertEqual(self.fields_dict['root measurement.depth.min'], '60 cm')

if __name__ == '__main__':
    unittest.main()
