# ADEPT
Automated Data Extraction for Plant Traits 


### Install in MAC m1/m2/m3

CFLAGS="-mavx -DWARN(a)=(a)" pip install nmslib

### Dev

pip install --editable .


<!-- python cli.py --file ../data/processing/input/peatland-species.csv --limit 4 --group angiosperm -->

 adept traits --file ../data/processing/input/peatland-species.csv --limit 4 --group angiosperm


  adept traits --taxa 'Anisotes trisulcus' --group angiosperm --ocr BHL
  adept traits --taxa 'Anisotes trisulcus' --group angiosperm --ocr BHL --force

adept traits --file  --group angiosperm --ocr BHL --force

  --file ../data/processing/input/peatland-species.csv

 adept traits --file ../data/processing/input/bryophyte_0623.xlsx --limit 4 --group angiosperm
  