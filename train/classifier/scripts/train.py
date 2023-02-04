
from pathlib import Path
from datasets import Dataset, DatasetDict, load_dataset
from transformers import AutoTokenizer, DataCollatorWithPadding
from transformers import TrainingArguments, AutoModelForSequenceClassification
from transformers import AdamW, get_scheduler
from torch.utils.data import DataLoader
from tqdm.auto import tqdm
import pandas as pd
import sklearn
import typer
import torch
import evaluate


from adept.bhl.tokenizer import load_tokenizer


def train(dataset_dir: Path, training_dir: Path, checkpoint: str):
    
    num_epochs = 1
    dataset = DatasetDict.load_from_disk(dataset_dir)
    tokenizer = load_tokenizer(checkpoint)    
    
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)  
    
    train_dataloader = DataLoader(
        dataset["train"], shuffle=True, batch_size=8, collate_fn=data_collator
    )
    eval_dataloader = DataLoader(
        dataset["validation"], batch_size=8, collate_fn=data_collator
    )
    
    model = AutoModelForSequenceClassification.from_pretrained(checkpoint, num_labels=2)
    
    optimizer = AdamW(model.parameters(), lr=5e-5)
     
    num_training_steps = num_epochs * len(train_dataloader)
    lr_scheduler = get_scheduler(
        "linear",
        optimizer=optimizer,
        num_warmup_steps=0,
        num_training_steps=num_training_steps,
    )    
    
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    model.to(device)
    
    progress_bar = tqdm(range(num_training_steps))

    model.train()
    for epoch in range(num_epochs):
        for batch in train_dataloader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            lr_scheduler.step()
            optimizer.zero_grad()
            progress_bar.update(1)    
    
    metric = evaluate.load("glue", "mrpc")
    model.eval()
    for batch in eval_dataloader:
        batch = {k: v.to(device) for k, v in batch.items()}
        with torch.no_grad():
            outputs = model(**batch)

        logits = outputs.logits
        predictions = torch.argmax(logits, dim=-1)
        metric.add_batch(predictions=predictions, references=batch["labels"])

    print(metric.compute()) 
    
    torch.save(model.state_dict(), training_dir / "state_dict_model.pt")   
    torch.save(model, training_dir / 'model.pt')
  
if __name__ == "__main__":    
    typer.run(train)
