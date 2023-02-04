import pandas as pd
import typer
import warnings
from pathlib import Path
from sklearn.model_selection import train_test_split
from datasets import Dataset, DatasetDict, load_dataset

import spacy
from spacy.tokens import DocBin
from adept.bhl.model import load_tokeniser

def convert(input_path: Path, output_dir: Path, checkpoint: str):

    df = pd.read_csv(input_path)
    # Rename the column is_desc to labels 
    df = df.rename(columns={"is_desc": "labels"}).astype({'labels':'int'})
    df = df.dropna()
    
    dataset = Dataset.from_pandas(df)
    tokenizer = load_tokeniser(checkpoint)
    
    train_test_dataset = dataset.train_test_split(test_size=0.1)
    _test_val_dataset = train_test_dataset['test'].train_test_split(test_size=0.5)    
    train_test_dataset['validation'] = _test_val_dataset['train']
    train_test_dataset['test'] = _test_val_dataset['test']    
    
    def tokenize_function(example):
        return tokenizer(example["text"], truncation=True, max_length=512)

    tokenized_datasets = train_test_dataset.map(tokenize_function, batched=True)      
    tokenized_datasets = tokenized_datasets.remove_columns(["text"])
    
    # Set dataset format to pytorch tensors
    tokenized_datasets.set_format("torch")          
    tokenized_datasets.save_to_disk(output_dir)

if __name__ == "__main__":    
    typer.run(convert)
