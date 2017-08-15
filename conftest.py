# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import time

import pytest

@pytest.fixture(scope="session")
def account():
    appid = os.environ.get("WECHAT_APPID")
    secret = os.environ.get("WECHAT_SECRET")
    assert appid is not None, "please set 'WECHAT_APPID' envrionment variable"
    assert secret is not None, "please set 'WECHAT_SECRET' envrionment variable"
    print("use wechat appid:%s, secret:%s" % (appid, secret))

    from yawxt import OfficialAccount
    return OfficialAccount(appid, secret)
    
@pytest.fixture(scope="session")
def openid(account):
    '''the best case is get an openid from ``next(account.get_users_iterator())``,
        however, due to wechat API quota limit,  the API often fails. we can set
        a WECHAT_OPENID environ variable to reduce the invoking of wechat 
        API'''
    _openid = os.environ.get("WECHAT_OPENID")
    assert _openid is not None, "please set 'WECHAT_OPENID' envrionment variable"
    return _openid
    
@pytest.fixture(scope="session")
def xml_builder(account, openid):
    from yawxt import Message
    def func(msg_type, content, msg_id = None):
        return Message(account.appid, openid, msg_id, msg_type, 
            content).build_xml()
    return func
    
@pytest.fixture(scope="session", autouse=True)
def statistic(pytestconfig):
    '''Statistics for wechat API usage in this test session'''
    
    yield
    from yawxt.api_wrapper import invoke_failure, invoke_success, OfficialAccount
    capmanager = pytestconfig.pluginmanager.getplugin('capturemanager')
    capmanager.suspendcapture()
    print()
    print()
    print("+++++API USAGE STATS++++++")
    for key in OfficialAccount.URLS:
        s, f = invoke_success[key], invoke_failure[key]
        print(key, s, f, s+f)
    print("+++++++++++++++++++++++")    
    capmanager.resumecapture()

