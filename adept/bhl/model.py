
import torch

from adept.config import MODEL_DIR
from adept.bhl.tokenizer import load_tokenizer


class TextClassifier:  

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    model = torch.load(MODEL_DIR / 'en_classifier-scibert.pt', map_location=torch.device(device))       
    tokenizer = load_tokenizer("allenai/scibert_scivocab_cased")

    def tokenise(self, text):
        return self.tokenizer(text, truncation=True, max_length=512, return_tensors='pt')
    
    def __call__(self, text):
        tokenised_text = self.tokenise(text)
        self.model.eval()

        with torch.no_grad():
            outputs = self.model(**tokenised_text)    

        logits = outputs.logits
        predictions = torch.argmax(logits, dim=-1)   

        return predictions.numpy().take(0)  

if __name__ == "__main__":
    TextClassifier()