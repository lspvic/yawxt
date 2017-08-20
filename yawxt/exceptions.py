# -*- coding: utf-8 -*-

from __future__ import unicode_literals

__all__ = ["APIError", "SemanticAPIError", "default_exceptions"]


class APIError(Exception):
    '''微信API调用异常类，通过 :class:`~yawxt.OfficalAccount` 调用微信API错误码
    不是0时抛出此异常

    :param errcode: 错误码，和微信全局错误码一致
    :param errmsg: 错误消息，微信API调用错误消息
    '''

    errcode = None
    errmsg = None

    def __init__(self, errcode, errmsg=None):
        self.errcode = errcode
        self.errmsg = errmsg


class ConcreteAPIError(APIError):

    def __init__(self, errmsg=None):
        self.errmsg = errmsg

    def __repr__(self):
        return "%s(errcode=%s, errmsg=%s)" % (
            self.__class__, self.errcode, self.errmsg)


class SystemAPIError(ConcreteAPIError):
    '''微信系统繁忙，此时请开发者稍候再试，错误码-1
    '''
    errcode = -1
    errmsg = "system error"


class MaxQuotaError(ConcreteAPIError):
    '''API日调用次数打到上限异常, 错误码45009
    '''
    errcode = 45009
    errmsg = "reach max api daily quota limit"


class ChangeIndustryError(ConcreteAPIError):
    '''改变模板消息行业API调用过于频繁，错误码43100
    '''
    errcode = 43100
    errmsg = "change template too frequently"


class SemanticAPIError(APIError):
    '''微信语义消息解析错误, 错误码7000000~8000000

    .. seealso:: :meth:`yawxt.WxClient.semantic_parse`
    '''
    errmsg = "semantic api error"


default_exceptions = {}


def _find_exceptions():
    for name, obj in globals().items():
        try:
            is_api_error = issubclass(obj, ConcreteAPIError)
        except TypeError:
            is_api_error = False
        if not is_api_error or obj.errcode is None:
            continue
        __all__.append(obj.__name__)
        old_obj = default_exceptions.get(obj.errcode, None)
        if old_obj is not None and issubclass(obj, old_obj):
            continue
        default_exceptions[obj.errcode] = obj


_find_exceptions()
del _find_exceptions
