
from pathlib import Path
import logging
import os
from dotenv import load_dotenv
from pint import UnitRegistry
from enum import Enum
import http.client


ROOT_DIR = Path(__file__).parent.parent.resolve()

DATA_DIR = Path(ROOT_DIR / 'data')

ASSETS_DIR = Path(DATA_DIR / 'assets')

MODEL_DIR = Path(DATA_DIR / 'models')
MODEL_DIR.mkdir(parents=True, exist_ok=True)

PROCESSING_DATA_DIR = Path(DATA_DIR / 'processing')

INPUT_DATA_DIR = Path(PROCESSING_DATA_DIR / 'input')
INPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

INTERMEDIATE_DATA_DIR = Path(PROCESSING_DATA_DIR / 'intermediate')
INTERMEDIATE_DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DATA_DIR = Path(PROCESSING_DATA_DIR / 'output')
OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

CACHE_DIR = Path(ROOT_DIR / '.cache')
CACHE_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path(ROOT_DIR / '.log')
LOG_DIR.mkdir(parents=True, exist_ok=True)


load_dotenv(ROOT_DIR / '.env')

class OCR(Enum):
    BHL = "BHL"
    TESSERACT = "TESSERACT"


class TaxonomicGroup(str, Enum):
    angiosperm = "angiosperm"
    bryophyte = "bryophyte"
    pteridophyte = "pteridophyte"
    gymnosperm = "gymnosperm"

unit_registry = UnitRegistry()
unit_registry.default_format = '~P'

# Convert all measurement values to CM (if not specified in a fields tpl file)
DEFAULT_MEASUREMENT_UNIT = 'cm'

DimensionType = Enum('DimensionType', ['LENGTH', 'WIDTH', 'HEIGHT', 'DEPTH', 'DIAMETER', 'RADIUS'])

measurement_units = ['cm', 'ft', 'm', 'meter', 'metre', 'km', 'kilometer', 'kilometre', 'centimeter', 'centimetre', 'mm', 'millimeter', 'millimetre', 'um', 'µm', 'micrometer', 'micrometre', 'micron', 'nm', 'nanometer', 'nanometre', 'pm', 'inch', 'feet', 'foot']

fields_template = ASSETS_DIR / 'fields.tpl.yml'




# Set up logging - inherit from luigi so we use the same interface
logger = logging.getLogger('luigi-interface')

# logger = logging.getLogger('adept')

# Capture all log levels, but handlers below set their own levels
# logger.setLevel(logging.ERROR)

# Set up file logging for errors and warnings
file_handler = logging.FileHandler(LOG_DIR / 'error.log')
file_handler.setFormatter(
    logging.Formatter("[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s")
)
# Log errors to files
file_handler.setLevel(logging.WARNING)
logger.addHandler(file_handler)

# Set up file logging for errors and warnings
debug_file_handler = logging.FileHandler(LOG_DIR / 'debug.log')
debug_file_handler.setLevel(logging.DEBUG)
logger.addHandler(debug_file_handler)


# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

class Settings:
  __conf = {
    "BHL_OCR_SOURCE": OCR[os.getenv('BHL_OCR_SOURCE', OCR.BHL)],
    # "BHL_API_KEY": os.getenv('BHL_API_KEY'),
    "BHL_OCR_ARCHIVE_PATH": Path(os.getenv('BHL_OCR_ARCHIVE')) if os.getenv('BHL_OCR_ARCHIVE') else None,
    "DESCRIPTION_SOURCES":  os.getenv('DESCRIPTION_SOURCES', 'BHL,EFLORAS,ECOFLORA').split(','),
    "DEBUG": os.getenv('DEBUG') or 0
  }

  __setters = ["BHL_OCR_SOURCE"]

  @staticmethod
  def get(name):
    return Settings.__conf[name]

  @staticmethod
  def set(name, value):
    if name in Settings.__setters:
      Settings.__conf[name] = value
    else:
      raise NameError("Name not accepted in set() method")


http.client.HTTPConnection.debuglevel = Settings.get('DEBUG')
