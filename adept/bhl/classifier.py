import spacy

class BHLClassifier:  

    threshold = 0.9

    def __init__(self) -> None:
        self.nlp = spacy.load('en_description_classifier')

    def is_description(self, text):
        predicted = self.nlp(text)
        return predicted.cats['description'] >= self.threshold
