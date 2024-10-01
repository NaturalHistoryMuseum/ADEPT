import ratarmountcore as rmc
import functools

from adept.config import Settings, logger
from pathlib import Path

class BHLOCRArchive:  

    def __init__(self, path: Path) -> None:
        logger.info('Opening BL ARCHIVE archive')
        self._archive = rmc.open(str(path), recursive=True)
        self._root_dir = list(self._archive.listDir("/").keys())[0]

    def get_text(self, page_id, item_id, seq_order):
        file_path = self._get_file_path(page_id, item_id, seq_order)
        if info := self._archive.getFileInfo(file_path):
            with self._archive.open(info) as f:
                return f.read()
 
    def _get_file_path(self, page_id, item_id, seq_order):
        page_id = str(page_id).zfill(8)
        item_id = str(item_id).zfill(6)
        seq_order = str(seq_order).zfill(4)
        return f'{self._root_dir}/{item_id[:3]}/{item_id}/{item_id}-{page_id}-{seq_order}.txt'

if __name__ == "__main__":    
    import time
    start = time.time()
    ocr = BHLOCRArchive(Settings.get('BHL_OCR_ARCHIVE_PATH'))
    text = ocr.get_text(page_id = 63526627, item_id = 334580, seq_order = 175) 
    stop = time.time()
    print(stop-start)   