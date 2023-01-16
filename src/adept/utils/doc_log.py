from asyncio.log import logger
from spacy import displacy
from traits.config import LOG_DIR

from traits.config import logger

class DocLog():
    
    """
    Log docs to html
    """
       
    HTML_LOG_DIR = LOG_DIR / 'html'
    HTML_LOG_DIR.mkdir(parents=True, exist_ok=True)       
    
    def __init__(self):
        
        logger.info("Writing HTML doc log to %s", self.HTML_LOG_DIR)
        
        # Delete everything in the html log directory
        [f.unlink() for f in self.HTML_LOG_DIR.glob("*") if f.is_file()]
        
    def log(self, doc, identifier, options={}):              
        html = displacy.render(doc, style='ent', page=True, jupyter=False, options=options)   
        log_file = self.HTML_LOG_DIR / f'{identifier}.html'    
        
        with log_file.open("a") as f:
            f.write(html)                