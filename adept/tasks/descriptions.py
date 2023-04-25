import luigi
from traitlets import default
import json
from pathlib import Path
import yaml

from adept.config import OCR_MODEL, INTERMEDIATE_DATA_DIR
from adept.tasks.description.ecoflora.description import EcofloraDescriptionTask
from adept.tasks.description.bhl.description import BHLDescriptionTask
from adept.tasks.description.efloras.description import EflorasChinaDescriptionTask, EflorasMossChinaDescriptionTask, EflorasNorthAmericaDescriptionTask, EflorasPakistanDescriptionTask
from adept.pipeline import Pipeline
from adept.config import TaxonomicGroup, logger, fields_template
from adept.tasks.base import BaseTask
from adept.utils.helpers import is_binomial


class DescriptionsTask(BaseTask):
        
    taxon = luigi.Parameter()  
    taxonomic_group = luigi.EnumParameter(enum=TaxonomicGroup)  
    template_path = luigi.OptionalPathParameter(default=fields_template)       
    pipeline = Pipeline()

    def requires(self):
        yield from [
            EcofloraDescriptionTask(taxon=self.taxon),
            EflorasNorthAmericaDescriptionTask(taxon=self.taxon),
            EflorasChinaDescriptionTask(taxon=self.taxon),
            EflorasMossChinaDescriptionTask(taxon=self.taxon),
            EflorasPakistanDescriptionTask(taxon=self.taxon),            
        ]
        if is_binomial(self.taxon):
            yield BHLDescriptionTask(taxon=self.taxon)
        
    def run(self):        
        field_mappings = self._get_tpl_field_mappings() if self.template_path else None
        if field_mappings:
            logger.info('Using %s field mappings from %s for %s', self.taxonomic_group, self.template_path, self.taxon)
                
        data = []
        for i in self.input():       
            logger.info('Collecting descriptions for %s', self.taxon)            
            with i.open('r') as f:
                descriptions = yaml.full_load(f)                
                for description in descriptions:                                       
                    if text := description.get('text'):
                        fields = self.pipeline(text, self.taxonomic_group)                                       
                        if field_mappings:
                            record = fields.to_mapped_dict(field_mappings)
                        else:
                            record = fields.to_dict()
                        record['source'] = description['source']
                        # Additional source ID - e.g. BHL
                        record['source_id'] = description.get('source_id', None)
                        record['taxon'] = description['taxon']
                        data.append(record)

        with self.output().open('w') as f:            
            f.write(json.dumps(data, indent=4))

    def output(self):
        file_name = self.taxon.replace(' ', '-').lower()  
        # If a different template file is specified, the output is different  
        if self.template_path: file_name += f'-{self.template_path.stem}'        
        dir_path = INTERMEDIATE_DATA_DIR / 'descriptions' / OCR_MODEL.name.lower()
        dir_path.mkdir(parents=True, exist_ok=True)        
        return luigi.LocalTarget(dir_path / f'{file_name}.json')      
    
    def _get_tpl_field_mappings(self):
        with self.template_path.open('r') as f:
            tpl = yaml.full_load(f)                 
            return tpl.get(self.taxonomic_group, None)
                

if __name__ == "__main__":        
    luigi.build([DescriptionsTask(taxon='Holcus lanatus', taxonomic_group=TaxonomicGroup.angiosperm, force=True)], local_scheduler=True)  