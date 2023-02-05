import pandas as pd
import sqlite3
import uuid
import yaml
import numpy as np


from adept.config import RAW_DATA_DIR, taxonomic_groups
from adept.utils.helpers import get_words

class Traits():
    """ 
    Read the traits from functional traits database
    """
    
    parts_path = RAW_DATA_DIR / 'anatomical-parts.yml'
    anatomical_parts = yaml.full_load(parts_path.open())
    
    def __init__(self):
        self._connection = sqlite3.connect(RAW_DATA_DIR / "functional_traits.db")
        self.synonyms = self._select_synonyms()        
        self._df = self._get_db_traits()
        
    def get_discrete_traits(self, group=None):                
        df = self._get_traits_by_type('discrete', group)
        df = self._synonymise(df)
        # Get list of columns with syn and term removed. We use synonym as term col         
        cols = list(set(df.columns) - {'synonym', 'term'})
        df = pd.concat(
            [
                df[['term'] + cols],
                df[df.synonym.notnull()].explode('synonym')[['synonym'] + cols].rename(columns={'synonym': 'term'})
            ], ignore_index=True
        )
        df.drop_duplicates()
        df = self._set_unique(df)   
        return df
    
    def get_colour_traits(self, group=None):
        return self._get_traits_by_type('colour', group)    
    
    def get_unique_colour_terms(self, group=None):
        df = self.get_colour_traits(group)
        return df.term.unique()   
    
    def get_unique_discrete_terms(self, group=None):
        df = self._get_traits_by_type('discrete', group)
        # Use both terms and character values - if a character exists in the text
        # we want tofind and use it
        return np.concatenate([df.term.unique(), df.character.unique()])
            
    def _read_sql_query(self, sql):
        return pd.read_sql_query(sql, self._connection)
    
    def _get_db_traits(self):                   
        return pd.concat([self._get_db_group_traits(group) for group in taxonomic_groups])
            
    def _get_db_group_traits(self, group):
        df = getattr(self, f'_select_{group}_traits')()        
        df = self._stack_trait_columns(df)                
        df = self._normalise(df)        
        df = self._set_part(df)
        df = self._set_require_part(df)
        df = self._set_type(df)             
        df['group'] = group        
        return df

    def _select_angiosperm_traits(self):
        return self._select_traits_angiosperm_table()
    
    def _select_bryophyte_traits(self):
        # We want to select both the traits in the bryophyte table, and the ones in the angiosperm table with plant group = Bryophyte         
        return pd.concat([
            self._read_sql_query("SELECT * from bryophyte_traits"),
            self._select_traits_angiosperm_table('Bryophyte')
        ])
    
    def _select_pteridophyte_traits(self):
        # We want to select both the traits in the bryophyte table, and the ones in the angiosperm table with plant group = Bryophyte         
        return pd.concat([
            self._read_sql_query("SELECT * from pteridophyte_traits"),
            self._select_traits_angiosperm_table('Pteridophyte')
        ]) 
    
    def _select_gymnosperm_traits(self):
        """
        Gymnosperms are treated the same as angiosperms, and AC has just added a few extra gymnosperm-only traits to be combined with angiosperms
        """
        return pd.concat([
            self._select_traits_angiosperm_table(),
            self._select_traits_angiosperm_table('Gymnosperms')
        ])
    
    def _select_traits_angiosperm_table(self, plant_group='Angiosperms'):
        sql = f"SELECT * from angiosperm_traits WHERE \"Plants Group\"='{plant_group}' OR \"Plants Group\" IS NULL"
        return self._read_sql_query(sql)    
    
    def _select_synonyms(self):
        synonyms_df = self._read_sql_query("SELECT DISTINCT term, REPLACE(synonym, '_', '-') as synonym from plant_glossary_synonyms")  
        synonyms_df = synonyms_df.groupby('term')['synonym'].apply(set).reset_index().set_index('term') 
        return synonyms_df
        
    def _get_traits_by_type(self, trait_type, group = None):
        mask = self._df.type == trait_type
        if group:
            mask &= self._df.group == group
        return self._df[mask]        
                    
    def _stack_trait_columns(self, df):
        df['uuid'] = df.apply(lambda _: uuid.uuid4(), axis=1)
        char_trait_cols = ["character", "trait"]

        # Stack the table so all characterX and traitX columns are
        # combined into character and trait column
        df = pd.wide_to_long(df, char_trait_cols, i='uuid', j="x")

        df = df[['term', 'character', 'trait', 'required_parts']]
        df = df.reset_index(drop=True)
        df = df.drop_duplicates()
        # If char and trait are empty, the row didn't have trait2, trait3 etc.,
        df = df.dropna(subset=char_trait_cols) 
        return df
    
    def _synonymise(self, df):
        # Add synonyms column  
        return df.join(self.synonyms, 'term', 'left')
    
    def _normalise(self, df):
        cols = df.select_dtypes(object).columns
        df[cols] = df[cols].apply(lambda x: x.str.lower())  
        df = df.replace('_','-', regex=True)            
        return df
    
    def _set_require_part(self, df):         
        # Set require part to True if the required parts is not set to * AND we have a part         
        df['require_part'] = df.apply(lambda x: True if x['required_parts'] != '*' and pd.notnull(x['part']) else False, axis=1)
        required_parts_df = df[~df.required_parts.isin([None, '*'])]        
        # required_parts is a semicolon delimited string - so explode into mutiple rows, one each for the parts     
        required_parts_df = required_parts_df.assign(part=required_parts_df['required_parts'].str.split(';')).explode('part')
        df = pd.concat([
            df, 
            required_parts_df
        ])  
        df = df.drop('required_parts', axis=1)
        return df    
    
    def _set_unique(self, df):
        # Along with the terms explicity marked in the DB, double check for any duplcated terms
        # Where require part = True, an anatomical part will be required         
        duplicated = df[df.duplicated(subset=['term'], keep=False)].groupby('term').agg({'part':'nunique'})
        non_unique = duplicated[duplicated.part > 1].reset_index()
        # df['require_part'] = np.where((df.term.isin(non_unique.term)) | (df.is_multiple == True), True, False)     
        df['is_unique'] = np.where((~df.term.isin(non_unique.term)), True, False)           
        return df
    
    def _set_type(self, df):    
        df['type'] = df['trait'].map(lambda x: 'colour' if 'colour' in x else 'discrete')
        return df
    
    def _set_part(self, df):                    
        df['part'] = df['trait'].apply(self._parse_part)            
        # Set some custom parts e.g. indumentum should only apply if found on leaves
        df.loc[df['trait'] == 'indumentum', "part"] = 'leaf'        
        return df
        
    def _parse_part(self, trait):    
        for part in [trait, trait.split()[0]]:
            if part in self.anatomical_parts.keys():
                return part    
        

class SimpleTraitTextClassifier:    
    """
    Quick method to classify text as a description
    """
    
    traits = Traits()
        
    def __init__(self, min_terms=5, min_ratio=0.05):        
        self.min_terms = min_terms
        self.min_ratio = min_ratio
        self._trait_terms = self._to_lower_set(self.traits.get_unique_discrete_terms())
        
    def is_description(self, text):
        words = self._to_lower_set(get_words(text))
        matching_terms = words.intersection(self._trait_terms) if words else [] 
        if not (words or matching_terms):
            return False        
        
        ratio = len(matching_terms) / len(words) 
        # If the percentage of parts is greater than 5% (for short descriptions)
        if ratio >= self.min_ratio and len(matching_terms) >= self.min_terms:
            return True                
        
    @staticmethod
    def _to_lower_set(terms):
        return set([t.lower() for t in terms])
    

    
   
if __name__ == '__main__':
    traits = SimpleTraitTextClassifier()
    
    
    text = "Herbs to 50 cm tall, annual, much branched. Stems 4-angled, glabrous. Petiole 0.3-1 cm; leaf blade ovate-lanceolate, lanceolate, or narrowly elliptic, 1.5-7 × 1-2.5 cm, both surfaces glabrous, abaxially pale green, adaxially green, secondary veins 3-5 on each side of midvein, base attenuate and decurrent onto petiole, margin entire, apex acute to shortly acuminate."
    print(traits.is_description(text))
    
