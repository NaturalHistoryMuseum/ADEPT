import luigi


from adept.config import PROCESSED_DATA_DIR
from adept.traits import Traits
from adept.utils.patterns import Patterns


class TraitPatternsTask(luigi.Task):
    
    def run(self):
        traits = Traits()
        patterns = Patterns()

        for term in traits.get_unique_discrete_terms():            
            patterns.add(term, 'TRAIT')
            
        for term in traits.get_unique_colour_terms():            
            patterns.add(term, 'COLOUR')            
            
        patterns.to_jsonl(self.output().path)
         
    def output(self):
        return luigi.LocalTarget(PROCESSED_DATA_DIR / 'traits.jsonl')


if __name__ == "__main__":    
    luigi.build([TraitPatternsTask()], local_scheduler=True)   