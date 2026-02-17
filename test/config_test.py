import unittest


from adept.config import ASSETS_DIR, App, OCR

from helpers import config_test

class TraitsTest(unittest.TestCase):
    
    # def setUp(self):
    #     self.pipeline = Pipeline()

    def test_ploidy(self):  
        App.set("BHL_OCR_SOURCE", OCR.BHL)  
        print(config_test())
        print('test')
        
        # print(fields.to_dict())
        
        
        # RAW_DATA_DIR / 'fields.tpl.yml'




if __name__ == '__main__':
    unittest.main()
