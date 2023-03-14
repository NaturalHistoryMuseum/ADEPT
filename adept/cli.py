from typing import List, Optional
from pathlib import Path
import pandas as pd
import typer
import re
import typer
import luigi

from adept.config import taxonomic_groups
from adept.tasks.run import RunTask

class Interface():
        
    def __init__(self, file_path, taxon_column, group_column, taxa, taxon_group):
        if file_path:
            df = self._read_file(file_path)             
            taxon_column = self._get_file_column(df, taxon_column, 'taxon')
            group_column = self._get_file_column(df, group_column, 'group')                  
            df[taxon_column] = df[taxon_column].str.strip().str.lower()
            df[group_column] = df[group_column].str.strip().str.lower() 
            self._taxa = df.groupby(group_column)[taxon_column].agg(list)
        elif taxa and taxon_group:       
            self._taxa = {
                'taxon_group': taxa
            }
        else:
            self.error(f'Please specify either an input file, or taxa and taxon group') 
              
    def _get_file_column(self, df, col_name, col_type):
        
        # Filter columns to make best guess for taxon and group coloumns
        col_filters = {
            'taxon': lambda c: re.search(r'name|species', c.lower()),
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
                typer.secho(f'Using column {cols[0]} for {col_type} in file')
                return cols[0]
            self.error(f'Could not detect a column for {col_type} in file')
            
    def _read_file(self, file_path: Path):

        if file_path.suffix == '.csv':
            return pd.read_csv(file_path)
        elif file_path.suffix  in ['.xlsx']:
            return pd.read_excel(file_path)
        
        self.error('Only .csv and .xslx files are supported')            

    def error(msg, abort=True):
        typer.secho(msg, fg=typer.colors.RED)
        if abort: raise typer.Abort()               
  
    def __iter__(self):
        yield from self._taxa.items()            


def main(
    file_path: Optional[Path] = typer.Option(None,"--file"), 
    taxon_column: Optional[str] = None, 
    group_column: Optional[str] = None, 
    taxa: Optional[List[str]] = typer.Option(None),
    taxon_group: Optional[str] = None, 
    force: bool = typer.Option(False, "--force"),
    local_scheduler: bool = typer.Option(True)
    ):
    
    interface = Interface(file_path, taxon_column, group_column, taxa, taxon_group)
    
    for group, taxa in interface:
        if group not in taxonomic_groups:
            typer.secho(f'Taxonomic group {group} is not supported - ignoring', fg=typer.colors.MAGENTA)
            continue
        
        try:
            taxa = taxa[:10]
        except:
            pass
        
        typer.secho(f'Queuing run task for {group} with {len(taxa)} taxa', fg=typer.colors.GREEN)
        luigi.build([RunTask(taxa=taxa, taxonomic_group=group, force=force)], local_scheduler=local_scheduler) 
        
    typer.secho(f'Processing complete', fg=typer.colors.GREEN)


if __name__ == "__main__":
    typer.run(main)



#  luigi.build([AggregateFileTask(taxa=taxa, taxonomic_group='angiosperm', force=True)], local_scheduler=True) 