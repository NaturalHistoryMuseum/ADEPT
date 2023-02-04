
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


from adept.bhl.model import load_tokeniser



def evaluate(dataset_dir: Path, model_dir: Path, checkpoint:str):
    
    test_dataset = Dataset.load_from_disk(dataset_dir / 'test')
    tokenizer = load_tokeniser(checkpoint)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    test_dataloader = DataLoader(
        test_dataset, batch_size=500, collate_fn=data_collator
    )    
    
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    model = torch.load(model_dir / 'en_classifier-scibert.pt', map_location=torch.device(device))
    model.eval()    
    
    model.to(device)
    
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
    print(sklearn.metrics.classification_report(y_test, y_pred, target_names=['0', '1']))    
    
    cm = sklearn.metrics.confusion_matrix(y_test, y_pred, labels=[0, 1])
    cm = ConfusionMatrixDisplay(cm, display_labels=[0, 1]).plot()
    cm.figure_.savefig('confusion_matrix.png')
    
    
if __name__ == "__main__":    
    typer.run(evaluate)