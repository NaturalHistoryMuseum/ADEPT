# ADEPT
Automated Data Extraction for Plant Traits 


## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

#### Install uv (if needed)
```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

#### Create a virtual environment
```bash
uv venv --python 3.11
```

#### Activate it (macOS/Linux)
```bash
source .venv/bin/activate
```

#### Install ADEPT from GitHub
```bash
uv pip install git+https://github.com/NaturalHistoryMuseum/ADEPT.git
```

## Install assets

#### BHL Names Index (required)

Creates an index of taxa occurences on BHL pages, constructed from BHL data downloads.

```
adept assets bhl-names
```

# BHL OCR Archive (optional - but highly recommended)

Download a copy of the BHL Optical Character Recognition (OCR) - Full Text Export.

Richard, Joel; Dearborn, Jacqueline (2022). BHL Optical Character Recognition (OCR) - Full Text Export (new). Smithsonian Libraries and Archives. Dataset. https://doi.org/10.25573/data.21422193.v22

If a local copy of the BHL text isn't available, the system will use the BHL API to download each page of text, impacting performance. 

```
adept assets bhl-names
```



# CLI

A CLI Interface is provided to run ADEPT


## Traits


#### Generate trait matrix for species *Anisotes trisulcus*

```
adept traits --taxa 'Anisotes trisulcus' --group angiosperm
```

#### Generate trait matrix for species *Anisotes trisulcus* using tesseract OCR, rather than BHL

```
adept traits --taxa 'Anisotes trisulcus' --group angiosperm --ocr TESSERACT
```

#### Generate trait matrix for first 4 species in example input file

```
 adept traits --file ../data/examples/angiosperm-10.xlsx --limit 4 --group angiosperm
```



<!-- python cli.py --file ../data/processing/input/peatland-species.csv --limit 4 --group angiosperm -->

 adept traits --file ../data/processing/input/peatland-species.csv --limit 4 --group angiosperm


  adept traits --taxa 'Anisotes trisulcus' --group angiosperm --ocr BHL
  adept traits --taxa 'Anisotes trisulcus' --group angiosperm --ocr BHL --force

adept traits --file  --group angiosperm --ocr BHL --force

  --file ../data/processing/input/peatland-species.csv

 adept traits --file ../data/processing/input/bryophyte_0623.xlsx --limit 4 --group angiosperm
  


adept traits --file ~/Projects/ADEPT/Data/angiosperm-10.xlsx --group angiosperm --ocr TESSERACT  


### OCR

By default, ADEPT uses BHL's own OCR text.  Known to have errors in it's OCR prcoessing, which impacts reliability of downstream metrics.

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
