
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
TRAINING_DIR = Path(DATA_DIR / 'training')
PACKAGES_DIR = Path(DATA_DIR / 'packages')
MODEL_DIR = Path(DATA_DIR / 'models')

PROCESSING_DATA_DIR = Path(ROOT_DIR / 'processing')
INPUT_DATA_DIR = Path(PROCESSING_DATA_DIR / 'input')
INTERMEDIATE_DATA_DIR = Path(PROCESSING_DATA_DIR / 'intermediate')
OUTPUT_DATA_DIR = Path(PROCESSING_DATA_DIR / 'output')









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

measurement_units = ['cm', 'ft', 'm', 'meter', 'metre', 'km', 'kilometer', 'kilometre', 'centimeter', 'centimetre', 'mm', 'millimeter', 'millimetre', 'um', 'µm', 'micrometer', 'micrometre', 'micron', 'nm', 'nanometer', 'nanometre', 'pm', 'inch']


DEBUG = os.getenv('DEBUG') or 0


http.client.HTTPConnection.debuglevel = DEBUG

# Set up logging
logging.root.handlers = []

logger = logging.getLogger()

# # Capture all log levels, but handler below set their own levels
# logger.setLevel(logging.INFO)

# # Set up file logging for errors and warnings
# file_handler = logging.FileHandler(LOG_DIR / 'error.log')
# file_handler.setFormatter(
#     logging.Formatter("[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s")
# )
# # Log errors to files
# file_handler.setLevel(logging.WARNING)
# logger.addHandler(file_handler)

# set up logging to console
console_handler = logging.StreamHandler()
# Simpler console utput
# console_handler.setFormatter(
#     logging.Formatter('%(levelname)-8s:\t%(message)s')
# )
# # Log debug+ to console
# console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
logger.addHandler(console_handler)


# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True






