from adept.config import MODEL_DIR, CACHE_DIR,logger
from transformers import AutoTokenizer
import torch

def load_tokeniser(checkpoint):
    
    tokeniser_path = CACHE_DIR / checkpoint.replace('/', '-')
    if tokeniser_path.exists():
        tokenizer = AutoTokenizer.from_pretrained(tokeniser_path)
    else:
        tokenizer = AutoTokenizer.from_pretrained(checkpoint)
        tokenizer.save_pretrained(tokeniser_path)              
    return tokenizer

class TextClassifier:  

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    
    if (MODEL_DIR / 'en_classifier-scibert.pt').exists():
        model = torch.load(MODEL_DIR / 'en_classifier-scibert.pt', map_location=torch.device(device))
    else:
        logger.critical('Text classifier model not found %s' % MODEL_DIR / 'en_classifier-scibert.pt')
        
    tokenizer = load_tokeniser("allenai/scibert_scivocab_cased")

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