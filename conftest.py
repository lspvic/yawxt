# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os

import pytest


@pytest.fixture(scope="session")
def client():
    '''微信公众号API调用 :class:`WxClient` fixture, appid和appsecret分别从
    环境变量 ``WECHAT_OPENID`` 和 ``WECHAT_SECRET`` 中获取
    '''

    appid = os.environ.get("WECHAT_APPID")
    secret = os.environ.get("WECHAT_SECRET")
    assert appid is not None, (
        "please set 'WECHAT_APPID' envrionment variable")
    assert secret is not None, (
        "please set 'WECHAT_SECRET' envrionment variable")

    from yawxt import WxClient
    return WxClient(appid, secret)


@pytest.fixture(scope="session")
def openid(client):
    '''openid fixture, 得到一个公众号关注的openid，从环境变量 ``WECHAT_OPENID``
    中获取

        .. note::

        The best case is get an openid from
        ``next(client.get_openid_iter())`` , however, due to wechat API
        quota limit,  the API often fails. we can set a WECHAT_OPENID
        environ variable to reduce the invoking of wechat API'''

    _openid = os.environ.get("WECHAT_OPENID")
    assert _openid is not None, (
        "please set 'WECHAT_OPENID' envrionment variable")
    return _openid


@pytest.fixture(scope="session")
def xml_builder(client, openid):
    from yawxt import Message

    def func(msg_type, content, msg_id=None):
        return Message(
            client.appid, openid, msg_type,
            content, msg_id,).build_xml()

    return func


@pytest.fixture(scope="session", autouse=True)
def statistic(pytestconfig):
    '''Statistics for wechat API usage in this test session'''

    yield
    from yawxt.client import invoke_failure, invoke_success, WxClient
    capmanager = pytestconfig.pluginmanager.getplugin('capturemanager')
    capmanager.suspendcapture()
    print()
    print()
    print("+++++API USAGE STATS++++++")
    for key in WxClient.URLS:
        s, f = invoke_success[key], invoke_failure[key]
        print(key, s, f, s+f)
    print("+++++++++++++++++++++++")
    capmanager.resumecapture()
