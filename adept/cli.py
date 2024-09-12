from typing import List, Optional
from pathlib import Path
import pandas as pd
import typer
import re
import typer
import luigi
import os
import time

from adept.config import TaxonomicGroup, Settings, OCR
from adept import config
from adept.tasks.traits import TraitsTask
from adept.tasks.descriptions import DescriptionsTask

class Interface():
        
    def __init__(self, file_path, taxon_column, group_column, taxa, taxon_group):

        if file_path:
            df = self._read_file(file_path)         
            if not (taxon_column := self._get_file_column(df, taxon_column, 'taxon')):
                self.error(f'Could not detect a column for taxon in file')
                
            df[taxon_column] = df[taxon_column].str.strip()
                        
            if group_column := self._get_file_column(df, group_column, 'group'):  
                df[group_column] = df[group_column].str.strip().str.lower()   
                if taxon_group:
                    df = df[df[group_column] == taxon_group.name]
                else:
                    groups = [g.name for g in TaxonomicGroup]
                    df = df[df[group_column].isin(groups)]      
                    
                self._taxa = df.groupby(group_column)[taxon_column].agg(list)            
                
            elif taxon_group:          
                self._taxa = {
                    taxon_group.name: df[taxon_column].unique().tolist()
                }             
            else:
                self.error(f'Could not detect a column for group in file')

        elif taxa and taxon_group:       
            self._taxa = {
                taxon_group.name: taxa
            }
        else:
            self.error(f'Please specify either an input file, or taxa and taxon group') 
            
        self.total = sum([len(t) for t in self._taxa.values()])
              
    def _get_file_column(self, df, col_name, col_type):
        
        # Filter columns to make best guess for taxon and group coloumns
        col_filters = {
            'taxon': lambda c: re.search(r'name|species|taxon|taxa', c.lower()),
            'group': lambda c: 'group' in c.lower()
        }  
              
        if col_name:
            if col_name in df.columns: 
                return col_name            
            self.error(f'A column named {col_name} is not present in file')            
        else:
            lambda_filter = col_filters[col_type]
            cols = list(filter(lambda_filter, df.columns))
            if len(cols) == 1: 
                typer.secho(f'Using column "{cols[0]}" for {col_type} in file')
                return cols[0]            
            
    def _read_file(self, file_path: Path):

        if file_path.suffix == '.csv':
            return pd.read_csv(file_path)
        elif file_path.suffix in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        
        self.error('Only .csv and .xslx files are supported')            

    @staticmethod
    def error(msg, abort=True):
        typer.secho(msg, fg=typer.colors.RED)
        if abort: raise typer.Abort()               
  
    def __iter__(self):
        yield from self._taxa.items()            


cli = typer.Typer()
count = 0

@cli.command("descriptions")
def descriptions(
    taxa: Optional[List[str]] = typer.Option(None), 
    force: bool = typer.Option(False, "--force"),
    local_scheduler: bool = typer.Option(True)):
    
    pass
    # luigi.build([AggregateDescriptionsTask(taxon_names=taxa, force=force)], local_scheduler=local_scheduler)

@cli.command("traits")
def traits(
    file_path: Optional[Path] = typer.Option(None,"--file"), 
    taxon_column: Optional[str] = None, 
    group_column: Optional[str] = None, 
    taxa: Optional[List[str]] = typer.Option(None),
    taxon_group: Optional[TaxonomicGroup] = typer.Option(None,"--group"), 
    force: bool = typer.Option(False, "--force"),
    ocr_source: Optional[OCR] = typer.Option(None,"--ocr"),
    rebuild_descriptions: bool = typer.Option(False, "--rebuild"),
    local_scheduler: bool = typer.Option(True),
    limit: Optional[int] = None
    ):

    interface = Interface(file_path, taxon_column, group_column, taxa, taxon_group)    
    typer.secho(f'Total of {interface.total} taxonomic names to process', fg=typer.colors.MAGENTA)  

    if ocr_source: 
        Settings.set('BHL_OCR_SOURCE', ocr_source)

    typer.secho(f"OCR Model: {Settings.get('BHL_OCR_SOURCE')}", fg=typer.colors.YELLOW) 

    def status_update(task):
        global count
        count += 1
        typer.secho(f'{count}/{interface.total}: {task.taxon} ({task.taxonomic_group}) complete', fg=typer.colors.GREEN)    
    
    @DescriptionsTask.event_handler(luigi.Event.SUCCESS)
    def on_success(task):
        status_update(task)
            
    @DescriptionsTask.event_handler(luigi.Event.DEPENDENCY_PRESENT)
    def on_dependency_present(task):
        status_update(task)     

    start = time.time()   

    for group, taxa in interface:
        
        # Per group limit, not total limit - but then can be combined with taxon_group
        if limit: taxa = taxa[:limit]

        typer.secho(f'Queuing run task for {group} with {len(taxa)} taxa', fg=typer.colors.GREEN)
        task = TraitsTask(taxa=taxa, taxonomic_group=TaxonomicGroup[group], force=force)
        if rebuild_descriptions: task.rebuild_descriptions()      
        
        luigi.build([task], local_scheduler=local_scheduler) 

    stop = time.time()



    typer.secho(f'Processing complete', fg=typer.colors.GREEN)
    typer.secho(f'Processing time: {stop-start}', fg=typer.colors.GREEN)

if __name__ == "__main__":
    cli()



#  luigi.build([AggregateFileTask(taxa=taxa, taxonomic_group='angiosperm', force=True)], local_scheduler=True) 