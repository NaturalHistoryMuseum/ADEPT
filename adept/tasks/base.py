import luigi
from pathlib import Path

class TaskMixin:
    
    force = luigi.BoolParameter(default=False, significant=False)
    output_dir = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)            
        if self.output_dir: 
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
    def complete(self):
        if self.force:
            return False
        
        return super().complete()               

class BaseExternalTask(TaskMixin, luigi.ExternalTask):
    pass

class BaseTask(TaskMixin, luigi.Task):
    pass    
