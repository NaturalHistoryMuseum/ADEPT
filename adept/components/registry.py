
from spacy.language import Language

from adept.components.sentencizer import SentencizerComponent
from adept.components.numeric import NumericComponent
from adept.components.anatomical import AnatomicalComponent
from adept.components.traits import CustomTraitsComponent, DiscreteTraitsComponent

@Language.factory("semicolon_sentencizer")
def create_sentencizer_component(nlp: Language, name: str):
    return SentencizerComponent(nlp)

@Language.factory("numeric")
def create_numeric_component(nlp: Language, name: str):
    return NumericComponent(nlp)

@Language.factory("anatomical_ner")
def create_anatomical_component(nlp: Language, name: str):
    return AnatomicalComponent(nlp)

@Language.factory("traits_ner")
def create_discrete_traits_component(nlp: Language, name: str):
    return DiscreteTraitsComponent(nlp)

@Language.factory("traits_custom_ner")
def create_numeric_traits_component(nlp: Language, name: str):
    return CustomTraitsComponent(nlp)


class ComponentsRegistry(object):
    def __init__(self, nlp):
        self.nlp = nlp
        
    def add_component(self, name: str, **kwargs):
        """
        Add a component
        name - the language factory name
        ** kwargs - matching https://spacy.io/api/language#add_pipe e.g. before='ner'
        
        """
        if not self.nlp.has_pipe(name):
            self.nlp.add_pipe(name, **kwargs)
        else:
            self.nlp.replace_pipe(name, name)  
