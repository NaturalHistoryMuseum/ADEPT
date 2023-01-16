import luigi
from traitlets import default
import json
from pathlib import Path

from adept.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, INTERMEDIATE_DATA_DIR
from adept.traits import Traits
from adept.utils.patterns import Patterns

from adept.tasks.descriptions.ecoflora import EcofloraDescriptionTask
from adept.tasks.descriptions.efloras import EflorasChinaDescriptionTask, EflorasMossChinaDescriptionTask, EflorasNorthAmericaDescriptionTask, EflorasPakistanDescriptionTask
from adept.pipeline import Pipeline
from adept.config import taxonomic_groups, logger



class PipelineTask(luigi.Task):
        
    taxon = luigi.Parameter()  
    taxonomic_group = luigi.ChoiceParameter(choices=taxonomic_groups, var_type=str, default="angiosperm")  
    template_path = luigi.PathParameter(default=RAW_DATA_DIR / 'fields.tpl.yml')       
    pipeline = Pipeline()

    def requires(self):
        return [
            EcofloraDescriptionTask(self.taxon),
            EflorasNorthAmericaDescriptionTask(self.taxon),
            EflorasChinaDescriptionTask(self.taxon)
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
              
        # with self.output().open('w') as f:
        #     # f.write(json.dumps(data, indent=4))
        #     pass

    def output(self):
        file_name = self.taxon.replace(' ', '-').lower()
        return luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'descriptions' / f'{file_name}.json')             
    
    

if __name__ == "__main__":    
    luigi.build([PipelineTask(taxon='Phalaris arundinacea'), PipelineTask(taxon='Isachne globosa')], local_scheduler=True)  