import unittest


from adept.pipeline import Pipeline


class PipelineTest(unittest.TestCase):
    
    def setUp(self):
        self.pipeline = Pipeline()

    def test_pipeline(self):  
        text = "Herbs to 40-100 cm tall, annual, much branched. 2 ovaries. 56 stamenoids. Seed volume is about 2 cm³."    
        fields = self.pipeline(text, 'angiosperm')
        print(fields.to_template())
        
        RAW_DATA_DIR / 'fields.tpl.yml'




if __name__ == '__main__':
    unittest.main()
