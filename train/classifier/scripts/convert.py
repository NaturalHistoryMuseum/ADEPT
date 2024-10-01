import pandas as pd
import typer
import warnings
from pathlib import Path
from sklearn.model_selection import train_test_split

import spacy
from spacy.tokens import DocBin


def convert(lang: str, input_path: Path, output_dir: Path):

    nlp = spacy.blank(lang)    
    df = pd.read_csv(input_path)    
    train, test = train_test_split(df, test_size=0.2, random_state=0, stratify=df.is_desc)

    doc_bin = to_doc_bin(nlp, train)
    doc_bin.to_disk(output_dir / "train.spacy")

    doc_bin = to_doc_bin(nlp, test)
    doc_bin.to_disk(output_dir / "test.spacy")    
    
def to_doc_bin(nlp, df):
    
    docs = []
    
    for doc, label in nlp.pipe(df.values.tolist(), as_tuples = True):
        doc.cats['description'] = label
        # Textcat classes must always equal 1 - so invert the label for not desc
        doc.cats['not_description'] = int(not(label))
        docs.append(doc)
    
    return DocBin(docs=docs)


if __name__ == "__main__":    
    typer.run(convert)
