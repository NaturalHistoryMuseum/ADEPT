from adept.config import CACHE_DIR
from transformers import AutoTokenizer

def load_tokenizer(checkpoint):
    
    tokenizer_path = CACHE_DIR / checkpoint.replace('/', '-')
    if tokenizer_path.exists():
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
    else:
        tokenizer = AutoTokenizer.from_pretrained(checkpoint)
        tokenizer.save_pretrained(tokenizer_path)              
    return tokenizer