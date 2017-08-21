# -*- coding:utf-8 -*-

import logging
import sys

from .client import WxClient
from .message import MessageHandler, check_signature
from .models import Message, User, Location
from .exceptions import *    # noqa


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

__all__ = [
    "WxClient", "MessageHandler", "Message", "User", "Location",
    "check_signature", "APIError", "SemanticAPIError", ]
__all__.extend(map(
    lambda cls: cls.__name__,
    default_exceptions.values()))    # noqa

__version__ = "0.1"
