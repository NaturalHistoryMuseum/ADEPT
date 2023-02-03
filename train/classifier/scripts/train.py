"""Convert entity annotation from spaCy v2 TRAIN_DATA format to spaCy v3
.spacy format."""
import pandas as pd
import typer
import warnings
from pathlib import Path
from sklearn.model_selection import train_test_split

import spacy
from spacy.tokens import DocBin
from transformers import AutoTokenizer

from adept.config import MODEL_DIR

class BHLDescriptionClassifier:  
    pass


def train():
    checkpoint = "bert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    
    # model = torch.load(MODEL_DIR / 'model.pt', map_location=torch.device('cpu'))



if __name__ == "__main__":    
    typer.run(train)
