import luigi
from traitlets import default
import json
from pathlib import Path
import yaml

from adept.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, INTERMEDIATE_DATA_DIR
from adept.traits import Traits
from adept.utils.patterns import Patterns

from adept.tasks.descriptions.ecoflora.description import EcofloraDescriptionTask
from adept.tasks.descriptions.bhl.description import BHLDescriptionTask
from adept.tasks.descriptions.efloras.description import EflorasChinaDescriptionTask, EflorasMossChinaDescriptionTask, EflorasNorthAmericaDescriptionTask, EflorasPakistanDescriptionTask
from adept.pipeline import Pipeline
from adept.config import taxonomic_groups, logger
from adept.tasks.base import BaseTask
from adept.utils.helpers import is_binomial


class PipelineTask(BaseTask):
        
    taxon = luigi.Parameter()  
    taxonomic_group = luigi.ChoiceParameter(choices=taxonomic_groups, var_type=str, default="angiosperm")  
    template_path = luigi.PathParameter(default=RAW_DATA_DIR / 'fields.tpl.yml')       
    pipeline = Pipeline()

    def requires(self):
        yield from [
            EcofloraDescriptionTask(taxon=self.taxon),
            # EflorasNorthAmericaDescriptionTask(taxon=self.taxon),
            # EflorasChinaDescriptionTask(taxon=self.taxon),
            # EflorasMossChinaDescriptionTask(taxon=self.taxon),
            # EflorasPakistanDescriptionTask(taxon=self.taxon),            
        ]
        if is_binomial(self.taxon):
            pass
            # yield BHLDescriptionTask(taxon=self.taxon)
        
    def run(self):
        data = []
        for i in self.input():       
            logger.info('Parsing descriptions for %s', self.taxon)            
            with i.open('r') as f:
                descriptions = yaml.full_load(f)
                
                
                for description in descriptions:                                           
                    if text := description.get('text'):
                        fields = self.pipeline(text, self.taxonomic_group)                    
                        if self.template_path:
                            record = fields.to_template(self.template_path)
                        else:
                            record = fields.to_dict()
                        record['source'] = description['source']
                        record['taxon'] = description['taxon']
                        data.append(record)

        with self.output().open('w') as f:            
            f.write(json.dumps(data, indent=4))

    def output(self):
        file_name = self.taxon.replace(' ', '-').lower()    
        return luigi.LocalTarget(INTERMEDIATE_DATA_DIR / 'descriptions' / f'{file_name}.json')             

if __name__ == "__main__":    
    luigi.build([PipelineTask(taxon='Potamogeton perfoliatus', force=True)], local_scheduler=True)  