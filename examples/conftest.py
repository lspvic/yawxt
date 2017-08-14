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
    return next(account.get_users_iterator())
    
@pytest.fixture(scope="session")
def xml_builder(account, openid):
    from yawxt import Message
    def func(msg_type, content, msg_id = None):
        return Message(account.appid, openid, msg_id, msg_type, 
            content).build_xml()
    return func