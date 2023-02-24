import spacy

from adept.components.registry import ComponentsRegistry
from adept.preprocess import Preprocess
from adept.postprocess import Postproccess
from adept.config import MODEL_DIR


class Pipeline():
    
    def __init__(self):

        # self.nlp = spacy.load("en_core_web_trf")        
        self.nlp = spacy.load(MODEL_DIR / 'adept')
        
        registry = ComponentsRegistry(self.nlp)        
        registry.add_component('numeric')
        registry.add_component('anatomical_ner')
        registry.add_component('traits_ner', after="anatomical_ner")
        registry.add_component('traits_custom_ner', after="traits_ner")
        registry.add_component('dimension_ner')
        registry.add_component('measurement_rel', after="dimension_ner")
                
        self.preprocess = Preprocess()        
        self.postprocess = Postproccess()  

    
    def __call__(self, text, taxon_group):            
        text = self.preprocess(text)          
        self.doc = self.nlp(text)
        return self.postprocess(self.doc, taxon_group)
    

