import spacy

from adept.components.registry import ComponentsRegistry
from adept.preprocess import Preprocess
from adept.postprocess import Postproccess
from adept.config import MODEL_DIR, logger


class Pipeline():
    
    def __init__(self):

        model = 'en_adept_ner_trf'

        # self.nlp = spacy.load("en_core_web_trf")        
        try:
            self.nlp = spacy.load(model)
        except OSError:
            print(f"Can't find model '{model}' - have you installed from train/ner/packages?")
            raise
        
        registry = ComponentsRegistry(self.nlp)       
        registry.add_component('numeric', after="ner")
        registry.add_component('anatomical_ner', after="ner")
        registry.add_component('traits_ner', after="ner")
        registry.add_component('traits_custom_ner', after="traits_ner")
        registry.add_component('dimension_ner', after="numeric")
        registry.add_component('measurement_rel', after="dimension_ner")  

        # registry.add_component('numeric')
        # registry.add_component('anatomical_ner')
        # registry.add_component('traits_ner', after="anatomical_ner")
        # registry.add_component('traits_custom_ner', after="traits_ner")
        # registry.add_component('dimension_ner')
        # registry.add_component('measurement_rel', after="dimension_ner")
                
        self.preprocess = Preprocess()        
        self.postprocess = Postproccess()  

    
    def __call__(self, text, taxon_group):            
        text = self.preprocess(text)          
        self.doc = self.nlp(text)
        return self.postprocess(self.doc, taxon_group)
    

