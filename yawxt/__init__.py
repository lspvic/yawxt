# -*- coding:utf-8 -*-

from .client import *
from .message import *
from .models import *
from .exceptions import *

__all__ = ["WxClient", "MessageHandler", "APIError",
    "Message", "User", "Location", "check_signature"]    
__all__.extend(map(lambda cls:cls.__name__, default_exceptions.values()))

__version__ = "0.1.dev1"