# ADEPT
Automated Data Extraction for Plant Traits 


### Install in MAC m1/m2/m3

CFLAGS="-mavx -DWARN(a)=(a)" pip install nmslib

### Dev




<!-- python cli.py --file ../data/processing/input/peatland-species.csv --limit 4 --group angiosperm -->

 adept traits --file ../data/processing/input/peatland-species.csv --limit 4 --group angiosperm


  adept traits --taxa 'Anisotes trisulcus' --group angiosperm --ocr BHL
  adept traits --taxa 'Anisotes trisulcus' --group angiosperm --ocr BHL --force

adept traits --file  --group angiosperm --ocr BHL --force

  --file ../data/processing/input/peatland-species.csv

 adept traits --file ../data/processing/input/bryophyte_0623.xlsx --limit 4 --group angiosperm
  


adept traits --file ~/Projects/ADEPT/Data/angiosperm-10.xlsx --group angiosperm --ocr TESSERACT  


### OCR

By default, uses BHL's own OCR text.  Known to have errors in it's OCR prcoessing, which impacts reliability of downstream metrics.

Users can choose to use Tesseract, downloading the page images from BHL, and extracting the text with Tesseract..

Add to .env file
BHL_OCR_SOURCE = 'TESSERACT'

Or specify at the command line with flag --ocr BHL


### Caching

Requests to BHL are cached. Two caching backends are supported - REDIS & SQLLITE.

SQLLITE is used by default, but is slightly slower for large numbers of requests.

docker compose up -d redis

Add to .env file
CACHE_BACKEND = 'REDIS'











TODO:

Readme