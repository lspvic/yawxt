# -*- coding: utf-8 -*-

'''Tests for OfficialAccount API'''

from __future__ import unicode_literals
import pytest
import os
from yawxt import  MaxQuotaError, ChangeIndustryError, User

@pytest.mark.xfail(raises=MaxQuotaError)
def test_get_users(account):
    openid = next(account.get_users_iterator())
    assert len(openid) > 0

@pytest.mark.xfail(raises=MaxQuotaError)
def test_users_count(account):
    assert account.get_users_count() > 0

@pytest.mark.xfail(raises=MaxQuotaError)
def test_get_user_info(account, openid):
    user = account.get_user_info(openid)
    assert isinstance(user, User)
    assert user.nickname is not None
    assert user.openid is not None
    
@pytest.mark.skip(reason='微信这个接口问题很多，无法测试')
def test_get_semantic(account, openid):
    info = account.get_user_info(openid)
    city = info["city"]
    query = "查一下明天从北京到上海的南航机票"
    result = account.get_semantic(query, city, uid=openid)
    assert "type" in result

@pytest.mark.xfail(raises=MaxQuotaError)    
def test_preview_message(account, openid):
    text = "能看到我发消息吗？"
    msg_id = account.preview_message(openid, text)
    assert msg_id is None
    
def test_js_ticket(account):
    print(account.js_ticket)
    assert account.js_ticket is not None
    
def test_js_config(account):
    url = "http://example.com"
    config = account.get_js_sign(url, debug = False)
    assert config["debug"] == "false"
    assert len(config["signature"]) == 40

@pytest.mark.xfail(raises=ChangeIndustryError)
def test_template_set_industry(account):
    account.set_industry(1,24)

@pytest.mark.xfail(raises=MaxQuotaError)    
def test_template_get_industry(account):
    result = account.get_industry()
    print(result)
    assert 'primary_industry' in result
    assert 'first_class' in result['primary_industry']
    assert 'secondary_industry' in result
    assert 'second_class' in result['secondary_industry']

@pytest.mark.xfail(raises=MaxQuotaError)
def test_template_add_template(account):
    template_id = account.add_template('TM00015')
    assert bool(template_id) is True

@pytest.mark.xfail(raises=MaxQuotaError)    
def test_template_all_list(account):
    result = account.get_template_list()
    assert isinstance(result, list)
    assert len(result) >= 1
    
@pytest.mark.xfail(raises=MaxQuotaError)
def test_template_send_message(account, openid):
    template_id = account.get_template_list()[0]['template_id']
    to_openid = openid
    data = {"first": {
                   "value":"恭喜你购买成功！",
                   "color":"#173177"},
               "orderMoneySum":{
                   "value":"28.85",
                   "color":"#173177"},
               "orderProductName": {
                   "value":"巧克力",
                   "color":"#173177"},
               "remark":{
                   "value":"欢迎再次购买！",
                   "color":"#173177"}
            }
    account.send_template_message(to_openid, template_id, data=data, url = "http://qq.com/")
    
@pytest.mark.xfail(raises=MaxQuotaError)
def test_template_del(account):
    template_id = account.get_template_list()[0]['template_id']
    account.delete_template(template_id)
    assert not template_id in map(
        lambda t:t["template_id"], account.get_template_list())