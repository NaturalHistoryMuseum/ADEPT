
from pathlib import Path
import logging
import os
from dotenv import load_dotenv
from pint import UnitRegistry
import http.client
import enum

ROOT_DIR = Path(__file__).parent.parent.resolve()

DATA_DIR = Path(ROOT_DIR / 'data')

ASSETS_DIR = Path(DATA_DIR / 'assets')
# TRAINING_DIR = Path(DATA_DIR / 'training')
# PACKAGES_DIR = Path(DATA_DIR / 'packages')
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
BHL_API_KEY = os.getenv('BHL_API_KEY')

taxonomic_groups = ['angiosperm', 'bryophyte', 'pteridophyte', 'gymnosperm']

unit_registry = UnitRegistry()
unit_registry.default_format = '~P'

DimensionType = enum.Enum('DimensionType', ['LENGTH', 'WIDTH', 'HEIGHT', 'DEPTH', 'DIAMETER', 'RADIUS'])

measurement_units = ['cm', 'ft', 'm', 'meter', 'metre', 'km', 'kilometer', 'kilometre', 'centimeter', 'centimetre', 'mm', 'millimeter', 'millimetre', 'um', 'µm', 'micrometer', 'micrometre', 'micron', 'nm', 'nanometer', 'nanometre', 'pm', 'inch', 'feet', 'foot']

fields_template = ASSETS_DIR / 'fields.tpl.yml'

DEBUG = os.getenv('DEBUG') or 0


http.client.HTTPConnection.debuglevel = DEBUG

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






