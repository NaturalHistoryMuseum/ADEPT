import spacy
from huggingface_hub import snapshot_download

from adept.components.registry import ComponentsRegistry
from adept.preprocess import Preprocess
from adept.postprocess import Postproccess
from adept.config import MODEL_DIR, logger

class Pipeline():
    
    def __init__(self):

        model = snapshot_download(
            repo_id="Benscott/en_adept_ner_trf",
            local_dir=MODEL_DIR,
            revision='857dba16758cc25e50dfd7a9d42795f4747f6394'
        )    
        self.nlp = spacy.load(model)    
        
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
    

