import spacy
from huggingface_hub import snapshot_download
from adept.config import MODEL_DIR

class BHLClassifier:  

    threshold = 0.9

    def __init__(self) -> None:
        model = snapshot_download(
            repo_id="Benscott/en_description_classifier",
            local_dir=MODEL_DIR,
            revision='d009096cdbfaf67526bb5187e7a980c1a765d984'
        )
        self.nlp = spacy.load(model)

    def is_description(self, text):
        predicted = self.nlp(text)
        return predicted.cats['description'] >= self.threshold
