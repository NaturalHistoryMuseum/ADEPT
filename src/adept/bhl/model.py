from adept.config import MODEL_DIR
from transformers import AutoTokenizer
import torch

# FIXME - Add map_location if not available
model = torch.load(MODEL_DIR / 'model.pt', map_location=torch.device('cpu'))

checkpoint = "allenai/scibert_scivocab_cased"
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR / 'scibert_scivocab_cased')

def predict(text):
    tokenised_text = tokenizer(text, truncation=True, max_length=512, return_tensors='pt')
    model.eval()
    
    with torch.no_grad():
        outputs = model(**tokenised_text)    
        
    logits = outputs.logits
    predictions = torch.argmax(logits, dim=-1)   
    
    return predictions.numpy().take(0)  