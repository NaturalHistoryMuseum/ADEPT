

from pathlib import Path
import requests
from tqdm import tqdm
import zipfile
import pandas as pd
from pydantic import AnyHttpUrl
import tarfile
import shutil
from urllib.parse import urlparse, parse_qs

from adept.config import CACHE_DIR, BHL_NAMES_INDEX_PATH, BHL_OCR_ARCHIVE_PATH, BHL_OCR_ARCHIVE_DOI


def _download_archive(url:AnyHttpUrl, target_path:Path):

    tmp_path = target_path.with_suffix(target_path.suffix + ".part")

    if target_path.exists():
        print(f"{target_path} already exists")
        return target_path
    
    headers = {"User-Agent": "Mozilla/5.0"}
    with requests.get(url, stream=True, allow_redirects=True, headers=headers) as r:
        r.raise_for_status()

        total = int(r.headers.get("content-length", 0))

        with open(tmp_path, "wb") as f, tqdm(
            total=total,
            unit="B",
            unit_scale=True,
            desc="Downloading BHL data",
        ) as bar:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))        

    tmp_path.rename(target_path)

    return target_path

def download_bhl_ocr_archive(archive_url):

    # # Get BHL redirections
    r = requests.get(archive_url, allow_redirects=True, stream=True, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()

    archive_target_path = CACHE_DIR / "bhl-ocr-archive-new.tar.bz2"

    return _download_archive(r.url, archive_target_path)

def create_bhl_ocr_text_archive(archive_url):

    bhl_ocr_tar_path = download_bhl_ocr_archive(archive_url)
    df = pd.read_parquet(CACHE_DIR / 'bhl_names.parquet')
    page_ids = set(df["PageID"].astype(str))    

    found = 0
    with tarfile.open(bhl_ocr_tar_path, "r:bz2") as tar, tqdm(total=50000000) as pbar:
        
        for member in tar:
            if member.isfile() and member.name.endswith(".txt"):
                page_id = member.name.rsplit("/", 1)[-1].split("-")[1]
                if page_id in page_ids:  
                    out_path = BHL_OCR_ARCHIVE_PATH / Path(member.name).name

                    f = tar.extractfile(member)
                    if f:        
                        with open(out_path, "wb") as out:
                            shutil.copyfileobj(f, out)
                    page_ids.remove(page_id)
                    found += 1
                    pbar.set_postfix(found=found)  

            pbar.update(1) 

def create_bhl_names_index(bhl_data_url, rebuild=False, echo=None):

    echo = echo or (lambda x, **_: None)

    # If file doesn't exist 
    if BHL_NAMES_INDEX_PATH.exists() and not rebuild:
        echo(f"{BHL_NAMES_INDEX_PATH} already exists")
        return
        
    BHL_ZIP_PATH = CACHE_DIR / "bhl_data.zip"

    echo(f"Downloading BHL data archive {bhl_data_url}")
    zip_path = _download_archive(bhl_data_url, BHL_ZIP_PATH)    

    echo(f"Reading data files from archive")

    with zipfile.ZipFile(zip_path) as z:

        echo(f"Extracting names")
        with z.open("BHL/pagename.txt") as f:    
            name_df = pd.read_csv(f, sep="\t", usecols=['PageID', 'NameConfirmed'])

        echo(f"Extracting pages")
        with z.open("BHL/page.txt") as f:    
            page_df = pd.read_csv(f, sep="\t", usecols=['PageID', 'ItemID', 'SequenceOrder'])            
            page_df = page_df.set_index('PageID')

        echo(f"Extracting items")
        with z.open("BHL/item.txt") as f:    
            item_df = pd.read_csv(f, sep="\t", usecols=['ItemID', 'TitleID'])            
            item_df = item_df.set_index('ItemID')

        echo(f"Extracting titles")
        with z.open("BHL/title.txt") as f:    
            title_df = pd.read_csv(f, sep="\t", usecols=['TitleID', 'LanguageCode'])            
            title_df = title_df.set_index('TitleID')    

        echo(f"Creating name index")        

        merged_df = item_df.join(title_df, on='TitleID')
        merged_df = page_df.join(merged_df, on='ItemID')
        merged_df = name_df.join(merged_df, on='PageID')

        # We only want eng lang
        merged_df = merged_df[merged_df.LanguageCode == 'ENG']

        merged_df = merged_df.drop(['LanguageCode'], axis=1)

        # Save index fle
        merged_df.to_parquet(BHL_NAMES_INDEX_PATH, index=False)


if __name__ == "__main__":    
    create_bhl_ocr_text_archive('https://ndownloader.figshare.com/files/52893371')


