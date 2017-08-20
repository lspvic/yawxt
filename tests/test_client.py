# -*- coding: utf-8 -*-

'''Tests for WxClient API'''

from __future__ import unicode_literals

import requests
import pytest
from yawxt import (
    MaxQuotaError, User, APIError, Location,
    ChangeIndustryError)


@pytest.mark.xfail(raises=MaxQuotaError)
def test_get_users(client):
    openid = next(client.get_openid_iter())
    assert len(openid) > 0


@pytest.mark.xfail(raises=MaxQuotaError)
def test_users_count(client):
    assert client.get_user_count() > 0


@pytest.mark.xfail(raises=MaxQuotaError)
def test_get_user_info(client, openid):
    user = client.get_user(openid)
    assert isinstance(user, User)
    assert user.nickname is not None
    assert user.openid is not None


def test_user_model(client, monkeypatch):
    info = {
            "subscribe": 1, 
            "openid": "o9KLls80ReakhjsbmHUZxjbz9K8c", 
            "nickname": "五音盒", 
            "sex": 1, 
            "language": "zh_CN", 
            "city": "杭州", 
            "province": "浙江", 
            "country": "中国", 
            "headimgurl": (
                "http://wx.qlogo.cn/mmopen/ajSDdqHZLLCXFhHOkecFpWDCW"
                "l5icpYpzzwc39E4nmyfSicjfg40EWSicf0R7VEDakCySlTybGJtWH4G"
                "53P01itBqA/0"), 
            "subscribe_time": 1440489434, 
            "remark": "", 
            "groupid": 0, 
            "tagid_list": [ ]}

    def mock_api_return(resp):
        return info

    monkeypatch.setattr(requests.Response, "json", mock_api_return)

    user = client.get_user(info["openid"])
    assert user.openid == info["openid"]
    assert user.nickname == info["nickname"]
    assert user.city == info["city"]
    assert user.province == info["province"]
    assert user.tagid_list == ""
    assert user.tagids == info["tagid_list"]
    assert user.subscribe == info["subscribe"]
    assert user.sex == info["sex"]
    assert user.language == info["language"]
    assert user.country == info["country"]
    assert user.headimgurl == info["headimgurl"]
    assert user.subscribe_time == info["subscribe_time"]
    assert user.remark == info["remark"]
    assert user.groupid == info["groupid"]


@pytest.mark.xfail(raises=APIError)
def test_semantic_parse(client, openid):
    info = client.get_user(openid)
    query = "查一下明天从北京到上海的南航机票"
    location = Location(23.1374665, 113.352425, openid=info.openid)
    result = client.semantic_parse(query, city=info.city, location=location)
    assert isinstance(result, dict)
    if "type" not in result:
        raise APIError(20701, str(result))


@pytest.mark.xfail(raises=MaxQuotaError)
def test_preview_message(client, openid):
    text = "能看到我发消息吗？"
    msg_id = client.preview_message(openid, text)
    assert msg_id is None


def test_js_config(client):
    url = "http://example.com"
    config = client.js_sign(url, debug=False)
    assert config["debug"] == "false"
    assert len(config["signature"]) == 40


@pytest.mark.xfail(raises=ChangeIndustryError)
def test_template_set_industry(client):
    client.set_industry(1, 24)


@pytest.mark.xfail(raises=MaxQuotaError)
def test_template_get_industry(client):
    result = client.get_industry()
    assert 'primary_industry' in result
    assert 'first_class' in result['primary_industry']
    assert 'secondary_industry' in result
    assert 'second_class' in result['secondary_industry']


@pytest.mark.xfail(raises=MaxQuotaError)
def test_template_add_template(client):
    template_id = client.add_sys_template('TM00015')
    assert bool(template_id) is True


@pytest.mark.xfail(raises=MaxQuotaError)
def test_template_all_list(client):
    result = client.get_template_list()
    assert isinstance(result, list)
    assert len(result) >= 1


@pytest.mark.xfail(raises=MaxQuotaError)
def test_template_send_message(client, openid):
    template_id = client.get_template_list()[0]['template_id']
    to_openid = openid
    data = {
        "first": {
           "value": "恭喜你购买成功！",
           "color": "#173177"},
        "orderMoneySum": {
           "value": "28.85",
           "color": "#173177"},
        "orderProductName": {
           "value": "巧克力",
           "color": "#173177"},
        "remark": {
           "value": "欢迎再次购买！",
           "color": "#173177"}
            }
    client.send_template_message(
        to_openid, template_id, data=data, url="http://qq.com/")


@pytest.mark.xfail(raises=MaxQuotaError)
def test_template_del(client):
    template_id = client.get_template_list()[0]['template_id']
    client.del_template(template_id)
    assert template_id not in map(
        lambda t: t["template_id"], client.get_template_list())
