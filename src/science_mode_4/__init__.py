"""Init file"""

from importlib.metadata import PackageNotFoundError, version

from .protocol import *
from .utils import *
from .general import *
from .low_level import *
from .mid_level import *
from .dyscom import *

from .device import *
from .layer import *
from .device_p24 import *
from .device_i24 import *

try:
    __version__ = version("science_mode_4")
    logger().info("science_mode_4 library version %s", __version__)
except PackageNotFoundError:
    pass
