
import logging

# Top-level imports
from .manager import DocumentManager # type: ignore
from .sources import * # type: ignore

# Configure logging per standard Python library recommendations
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())