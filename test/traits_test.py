import unittest


from adept.pipeline import Pipeline
from adept.config import RAW_DATA_DIR


class TraitsTest(unittest.TestCase):
    
    def setUp(self):
        self.pipeline = Pipeline()

    def test_ploidy(self):  
        text = "Herbs to 40-100 cm tall, annual, much branched. 2 ovaries. 56 stamenoids. Seed volume is about 2 cm³. 2n=23,34"    
        fields = self.pipeline(text, 'angiosperm')
        print(fields.to_template(RAW_DATA_DIR / 'fields.tpl.yml'))
        
        # print(fields.to_dict())
        
        
        # RAW_DATA_DIR / 'fields.tpl.yml'




if __name__ == '__main__':
    unittest.main()
