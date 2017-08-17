# -*- coding:utf-8 -*-

from .client import WxClient
from .message import MessageHandler, check_signature
from .models import Message, User, Location
from .exceptions import *    # noqa

__all__ = [
    "WxClient", "MessageHandler", "APIError", "Message",
    "User", "Location", "check_signature"]
__all__.extend(map(
    lambda cls: cls.__name__,
    default_exceptions.values()))    # noqa

__version__ = "0.1.dev1"
