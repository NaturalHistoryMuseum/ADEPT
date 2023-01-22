
from pathlib import Path
import logging
import os
from dotenv import load_dotenv
from pint import UnitRegistry
import http.client
import enum

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()

DATA_DIR = Path(ROOT_DIR / 'data')
RAW_DATA_DIR = Path(DATA_DIR / 'raw')
INTERMEDIATE_DATA_DIR = Path(DATA_DIR / 'intermediate')
PROCESSED_DATA_DIR = Path(DATA_DIR / 'processed')
PACKAGES_DATA_DIR = Path(DATA_DIR / 'packages')

CACHE_DIR = Path(ROOT_DIR / '.cache')
CACHE_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = Path(ROOT_DIR / '.log')
LOG_DIR.mkdir(parents=True, exist_ok=True)


taxonomic_groups = ['angiosperm', 'bryophyte', 'pteridophyte', 'gymnosperm']


# BHL_API_KEY = os.getenv('BHL_API_KEY')

# MONGO_CONNECTION_STRING = "mongodb://root:pass@localhost:27017"

unit_registry = UnitRegistry()
unit_registry.default_format = '~P'

measurement_units = ['cm', 'mm', 'm']


DEBUG = os.getenv('DEBUG')

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






