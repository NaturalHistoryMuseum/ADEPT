import sqlite3

from adept.config import logger, RAW_DATA_DIR

class WorldFlora():
    
    database = RAW_DATA_DIR / "wfo.db"
    
    # FIXME: DB file is too large for Github, so lets download it
    
    def __init__(self):
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        self.cursor = conn.cursor()
    
    def get_taxa_by_name(self, name):                
        sql = f"SELECT * FROM classification where scientificName=? and taxonRank IN ('SPECIES', 'VARIETY')"
        res = self._execute(sql, name)        
        return res.fetchall()         
    
    def get_taxon(self, taxon_id):
        sql = "SELECT * FROM classification where taxonID=?"
        res = self._execute(sql, taxon_id)  
        return res.fetchone()
    
    def get_synonyms(self, accepted_name_id):
        sql = f"SELECT * FROM classification where acceptedNameUsageID=? and taxonRank IN ('SPECIES')"
        res = self._execute(sql, accepted_name_id)
        return res.fetchall()  
    
    def _execute(self, sql, *args):
        return self.cursor.execute(sql, args)

    def get_related_names(self, name):
                
        taxa = self.get_taxa_by_name(name)
        
        if not taxa:
            logger.warning('Taxa %s not found in worldflora database', name)
            return
        elif len(taxa) > 1:
            logger.warning('Multiple taxa found in worldflora database for %s', name)
            return            
            
        taxon = dict(taxa[0])   

        taxon_status = taxon.get('taxonomicStatus', None)
        names = set()
        
        if taxon_status == 'ACCEPTED':
            synonyms = self.get_synonyms(taxon['taxonID'])
        elif taxon_status in ['SYNONYM', 'HOMOTYPICSYNONYM', 'HETEROTYPICSYNONYM']:
            accepted_name = self.get_taxon(taxon['acceptedNameUsageID'])
            names.add(accepted_name['scientificName'])
            synonyms = self.get_synonyms(accepted_name['taxonID'])
        else:
            return names

        names.update([syn['scientificName'] for syn in synonyms])
            
        return names