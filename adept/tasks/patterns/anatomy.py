import luigi
import yaml

from adept.config import ASSETS_DIR
from adept.utils.patterns import Patterns
from adept.tasks.base import BaseTask

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
        return luigi.LocalTarget(ASSETS_DIR / 'anatomical-parts.yml')


class AnatomyPatternsTask(BaseTask):
    
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
        return luigi.LocalTarget(ASSETS_DIR / 'anatomy-pattterns.jsonl')


if __name__ == "__main__":    
    luigi.build([AnatomyPatternsTask(force=True)], local_scheduler=True)   