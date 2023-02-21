import pandas as pd
from adept.config import logger, ASSETS_DIR

class WorldFlora():
    
    def __init__(self):
        # Read parquent file - keeps file size small enough to go into github         
        self._df = pd.read_parquet(ASSETS_DIR / 'worldflora.parquet') 
    
    def get_taxa_by_name(self, name):      
        return self._df[self._df['scientificName'] == name]
    
    def get_taxon_by_id(self, taxon_id):      
        df = self._df[self._df['taxonID'] == taxon_id]    
        return df.squeeze()
        
    def get_synonyms(self, accepted_name_id):      
        return self._df[(self._df['acceptedNameUsageID'] == accepted_name_id) & (self._df['taxonRank'] == 'SPECIES')]

    def get_related_names(self, name):
        df = self.get_taxa_by_name(name)
        if df.empty:
            logger.warning('Taxa %s not found in worldflora', name)
            return
        elif len(df.index) > 1:
            logger.warning('Multiple taxa found in worldflora for %s', name)
            return   
        
        taxon = df.squeeze()
        taxon_status = taxon['taxonomicStatus']

        names = set()
        if taxon_status == 'ACCEPTED':
            synonyms = self.get_synonyms(taxon['taxonID'])
        elif taxon_status in ['SYNONYM', 'HOMOTYPICSYNONYM', 'HETEROTYPICSYNONYM']:
            accepted_name = self.get_taxon_by_id(taxon['acceptedNameUsageID'])
            names.add(accepted_name['scientificName'])
            synonyms = self.get_synonyms(accepted_name['taxonID'])
        else:
            return
            
        names |= set(synonyms['scientificName'].unique().tolist())
            
        return names