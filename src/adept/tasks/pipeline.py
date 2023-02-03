import luigi
from traitlets import default
import json
from pathlib import Path

from adept.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, INTERMEDIATE_DATA_DIR
from adept.traits import Traits
from adept.utils.patterns import Patterns

from adept.tasks.descriptions.ecoflora.description import EcofloraDescriptionTask
from adept.tasks.descriptions.efloras.description import EflorasChinaDescriptionTask, EflorasMossChinaDescriptionTask, EflorasNorthAmericaDescriptionTask, EflorasPakistanDescriptionTask
from adept.pipeline import Pipeline
from adept.config import taxonomic_groups, logger
from adept.tasks.base import BaseTask


class PipelineTask(BaseTask):
        
    taxon = luigi.Parameter()  
    taxonomic_group = luigi.ChoiceParameter(choices=taxonomic_groups, var_type=str, default="angiosperm")  
    template_path = luigi.PathParameter(default=RAW_DATA_DIR / 'fields.tpl.yml')       
    pipeline = Pipeline()

    def requires(self):
        return [
            EcofloraDescriptionTask(taxon=self.taxon),
            EflorasNorthAmericaDescriptionTask(taxon=self.taxon),
            EflorasChinaDescriptionTask(taxon=self.taxon),
            EflorasMossChinaDescriptionTask(taxon=self.taxon),
            EflorasPakistanDescriptionTask(taxon=self.taxon),
        ]
        
    def run(self):
        data = []
        for i in self.input():
            
            # We need to know where the description came from - so get the 
            # lower directories of the file, relative to INTERMEDIATE_DATA_DIR
            # e.g. efloras/flora_of_north_america
            rel_path = Path(i.path).relative_to(INTERMEDIATE_DATA_DIR)
            source = str(rel_path.parents[0])
        
            logger.error('Parsing description for %s from source %s', self.taxon, source)
            
            with i.open('r') as f:
                record = {}
                if description := f.read():                    
                    fields = self.pipeline(description, self.taxonomic_group)                    
                    if self.template_path:
                        record = fields.to_template(self.template_path)
                    else:
                        record = fields.to_dict()
                else:
                    logger.error('No description for %s from source %s', self.taxon, source)
                    
                        
                record['source'] = source                   
                data.append(record)
              
        with self.output().open('w') as f:            
            f.write(json.dumps(data, indent=4))

    def output(self):
        file_name = self.taxon.replace(' ', '-').lower() 
        
        # FIXME: Could potentially break if dict is used - add dict to path
        # if not self.template_path:
        #     file_name = f'{file_name}-{self.template_path.stem}'     
        #     print(file_name)       
        return luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'descriptions' / f'{file_name}.json')             
    
    

if __name__ == "__main__":    
    luigi.build([PipelineTask(taxon='Amelanchier arborea', force=True)], local_scheduler=True)  