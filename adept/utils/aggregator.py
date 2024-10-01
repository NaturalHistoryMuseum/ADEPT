import re
import numpy as np
import itertools

class Aggregator():
    """
    Aggregate dataframe columns 
    """    
    num_unit_regex = re.compile('([\d\.]+)\s([a-z]+)')
    
    def _is_measurement_col(self, rows):
        return any([g for row in self._notnull(rows) if (g := self.num_unit_regex.match(row))])    
    
    def concat(self, rows):
        rows = self._notnull(rows)
        # Ploidy 2n contains , so we don't want to split or concatenate on ','     
        text_list = [s.split(',') for s in rows if not s.startswith('2n')]
        if text_list:
            return ', '.join(set([t.strip() for t in itertools.chain(*text_list)]))
            # return ', '.join(self._dedupe([t.strip() for t in itertools.chain(*text_list)]))
        else:
            return '| '.join(rows)  
        
    @staticmethod
    def _dedupe(terms):
        terms = set(terms)
        # If we have a term with a /, see if either of it's terms
        # already exist and then drop it
        # e.g. erect leafy/tussock should be dropped if either erect leafy or tussock exists
        with_slash = [t for t in terms if '/' in t]
        for slash_term in with_slash:
            if set(slash_term.split('/')) & terms:
                terms.discard(slash_term)

        return terms

    def mean_measurement(self, rows):
        return self._parse_measurement(rows, np.mean)

    def min_measurement(self, rows):
        return self._parse_measurement(rows, np.min)    

    def max_measurement(self, rows):
        return self._parse_measurement(rows, np.max)       
    
    def num_range(self, rows):
        rows = self._notnull(rows)
        if not rows.empty:
            min_ = min(rows)
            max_ = max(rows)
            if min_ == max_:
                return min_
            else:
                return f'{min_}-{max_}'    
    
    @staticmethod
    def _notnull(rows):
        return rows[rows.notnull()]
    
    def _parse_measurement(self, rows, agg_func):
        num_unit = [g for row in self._notnull(rows) if (g := self.num_unit_regex.match(row))]
        num = agg_func(np.array([float(n.group(1)) for n in num_unit])).round(2)
        unit = num_unit[0].group(2)
        return f'{num} {unit}'    

    def _get_numeric_aggregator(self, col, is_measurement):        
        if 'min' in col:
            return min if not is_measurement else self.min_measurement
        elif 'max' in col:
            return max if not is_measurement else self.max_measurement
        else:
            return self.num_range if not is_measurement else self.mean_measurement    
    
    def get_column_mappings(self, df, exclude=None):
        aggregators = {}
        for col in df.select_dtypes('number'):
            aggregators[col] = self._get_numeric_aggregator(col, False)
        
        for col in df.select_dtypes('object'): 
            if self._is_measurement_col(df[col]):
                aggregators[col] = self._get_numeric_aggregator(col, True)
            else:
                aggregators[col] = self.concat   
                
        if exclude:
            aggregators = {col: agg for col, agg in aggregators.items() if col not in exclude}
                            
        return aggregators