import spacy
from spacy.language import Language
from spacy.tokens import Doc


from adept.components.sentencizer import SentencizerComponent


@Language.component("semicolon_sentencizer")
def create_sentencizer_component(nlp: Language):
    return SentencizerComponent(nlp)



# OLD: To remove

class ComponentsRegistry(object):
    def __init__(self, nlp):
        self.nlp = nlp
        
    def add_components(self, components):                       
        for component in components: 
            self._register_component(component) 

        for component in components:  
            self._update_pipeline_component(component) 
                
    def add_component(self, component):    
        self._register_component(component)
        self._update_pipeline_component(component)         

    def _register_component(self, component):  
        if not Language.has_factory(component.name):  
            @Language.factory(component.name)
            def add_factory_component(nlp, name):
                return component(nlp)            

    def _update_pipeline_component(self, component):   
        if not self.nlp.has_pipe(component.name):
            self.nlp.add_pipe(component.name, **component.pipeline_config)
        else:
            self.nlp.replace_pipe(component.name, component.name)      
