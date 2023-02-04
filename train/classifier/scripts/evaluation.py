
from pathlib import Path
from datasets import Dataset, DatasetDict, load_dataset
from transformers import AutoTokenizer, DataCollatorWithPadding
from transformers import TrainingArguments, AutoModelForSequenceClassification
from transformers import AdamW, get_scheduler
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import sklearn
import typer
import torch
import json


from adept.bhl.tokenizer import load_tokenizer


def evaluate(dataset_dir: Path, training_dir: Path, checkpoint: str):  
    
    model_path = training_dir / 'model.pt'
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    model = torch.load(model_path, map_location=torch.device(device))
    model.eval()        
    model.to(device)
    
    test_dataset = Dataset.load_from_disk(dataset_dir / 'test')    
    tokenizer = load_tokenizer(checkpoint)        
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)  
    
    test_dataloader = DataLoader(
        test_dataset, shuffle=True, batch_size=8, collate_fn=data_collator
    )    
    
    for batch in test_dataloader:
        batch = {k: v.to(device) for k, v in batch.items()}
        with torch.no_grad():
            outputs = model(**batch)

        logits = outputs.logits
        predictions = torch.argmax(logits, dim=-1)                
        y_test = batch["labels"]
        break
    
    y_pred = predictions.cpu().detach().numpy()
    y_test = y_test.cpu().detach().numpy()
    
    
    class_report = sklearn.metrics.classification_report(y_test, y_pred, target_names=['0', '1'])
    
    print(class_report)
    
    with (training_dir / 'confusion_matrix.png').open('w') as f:
        json.dump(class_report, f)    
    
    cm = sklearn.metrics.confusion_matrix(y_test, y_pred, labels=[0, 1])
    cm = ConfusionMatrixDisplay(cm, display_labels=[0, 1]).plot()
    cm.figure_.savefig(training_dir / 'confusion_matrix.png')
    
    print(cm)
    
    
if __name__ == "__main__":    
    typer.run(evaluate)