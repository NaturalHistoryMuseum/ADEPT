import luigi


from adept.config import OUTPUT_DATA_DIR
from adept.traits import Traits
from adept.utils.patterns import Patterns
from adept.tasks.base import BaseTask


class TraitPatternsTask(BaseTask):
    
    def run(self):
        traits = Traits()
        patterns = Patterns()

        for term in traits.get_unique_discrete_terms():            
            patterns.add(term.strip(), 'TRAIT')
            
        for term in traits.get_unique_colour_terms():            
            patterns.add(term.strip(), 'COLOUR')            
            
        patterns.to_jsonl(self.output().path)
         
    def output(self):
        return luigi.LocalTarget(OUTPUT_DATA_DIR / 'traits.jsonl')


if __name__ == "__main__":    
    luigi.build([TraitPatternsTask(force=True)], local_scheduler=True)   