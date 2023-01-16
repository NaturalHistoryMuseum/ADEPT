from dataclasses import dataclass, field
from typing import List, Set
from pathlib import Path
import jsonlines
import re

@dataclass
class Patterns:
    
    _patterns: Set[tuple] = field(init=False, default_factory=set)
    match_attr: List = field(default_factory=lambda: ['lower', 'lemma'])
    
    def add(self, term, label):
        self._patterns.add((term, label))
                    
    def to_jsonl(self, path: Path):
        with jsonlines.open(path, mode='w') as writer:
            for term, label in self._patterns:
                for match in self.match_attr:
                    writer.write({
                        'label': label,
                        'pattern': [{match: t} for t in term.split()]
                    })
                    if '-' in term:                        
                        writer.write({
                            'label': label,
                            # We split using regex \w so the '-' stays in the pattern
                            'pattern': [{match: t} for t in re.split('(\W)', term)]
                        })
                        break
        
