"""Convert entity annotation from spaCy v2 TRAIN_DATA format to spaCy v3
.spacy format."""
import pandas as pd
import typer
import warnings
from pathlib import Path
from sklearn.model_selection import train_test_split

import spacy
from spacy.tokens import DocBin

from adept.config import DATA_DIR


def convert(lang: str, input_path: Path, output_dir: Path):
    df = pd.read_json(input_path)
    df.columns = ['sent', 'entities']
    def _get_label(entities):
        labels = {e[2] for e in entities['entities']}
        return next(iter(labels)) if len(labels) == 1 else 'MULTI'

    df['label'] = df['entities'].apply(_get_label)
    
    train, test = train_test_split(df, test_size=0.3, random_state=0, stratify=df[['label']])
    test, val = train_test_split(test, test_size=0.5, random_state=0, stratify=test[['label']])

    for name, data in [('train', train), ('test', test), ('val', val)]:
        write_spacy_doc_bin(lang, data, output_dir / f'{name}_numeric.spacy')
    
    
def write_spacy_doc_bin(lang: str, df: pd.DataFrame, output_path: Path):
    
    nlp = spacy.blank(lang)
    db = DocBin()
    for text, annot in df[['sent', 'entities']].values:
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in annot["entities"]:
            span = doc.char_span(start, end, label=label)
            if span is None:
                msg = f"Skipping entity [{start}, {end}, {label}] in the following text because the character span '{doc.text[start:end]}' does not align with token boundaries:\n\n{repr(text)}\n"
                warnings.warn(msg)
            else:
                ents.append(span)
        doc.ents = ents
        db.add(doc)

    db.to_disk(output_path)


if __name__ == "__main__":
    
    typer.run(convert)
