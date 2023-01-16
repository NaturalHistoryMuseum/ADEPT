import luigi
import yaml

from adept.config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from adept.traits import Traits
from adept.utils.patterns import Patterns

class AnatomicalPartsTask(luigi.ExternalTask):
    """
    External File: anatomical-parts.yml
    """
    def output(self):
        """
        Returns file target anatomical-parts.yml
        :return: the target output for this task.
        :rtype: object (:py:class:`luigi.target.Target`)
        """
        return luigi.LocalTarget(RAW_DATA_DIR / 'anatomical-parts.yml')


class AnatomyPatternsTask(luigi.Task):
    
    def requires(self):
        """
        This task's dependencies:
        * :py:class:`~.AnatomicalParts`
        :return: list of object (:py:class:`luigi.task.Task`)
        """
        return AnatomicalPartsTask()  
    
    def _read_anatomical_parts(self):
        f = yaml.full_load(self.input().open())
        for term, synonym in f.items():
            yield term
            if synonym:
                yield from synonym 
            else:
                yield f'{term}s'    
    
    def run(self):
        patterns = Patterns()
        for part in self._read_anatomical_parts():
            patterns.add(part, 'PART')
            
        patterns.to_jsonl(self.output().path)
         
    def output(self):
        return luigi.LocalTarget(PROCESSED_DATA_DIR / 'anatomy.jsonl')


if __name__ == "__main__":    
    luigi.build([AnatomyPatternsTask()], local_scheduler=True)   