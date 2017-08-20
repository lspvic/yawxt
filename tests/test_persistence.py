# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import time

import pytest
import requests

from yawxt.persistence import PersistMessageHandler
from yawxt.models import User, Location, Message


@pytest.fixture(autouse=True)
def handler(client, DB_Session, xml_builder):
    xml_text = xml_builder(
        "text", "<Content><![CDATA[this is a test]]></Content>",
        msg_id=1234567890123456)
    handler = PersistMessageHandler(
        xml_text, client, db_session_maker=DB_Session,
        debug_to_wechat=True)
    handler.reply()
    return handler


def test_message_save(client, xml_builder, DB_Session, db_session, openid):
    xml_text = xml_builder(
        "text", "<Content><![CDATA[this is a test]]></Content>",
        msg_id=234567890)
    handler = PersistMessageHandler(
        xml_text, client,
        db_session_maker=DB_Session, debug_to_wechat=True)
    handler.reply()
    message = (
        db_session.query(Message)
        .filter_by(msg_id=234567890, from_id=openid).first())
    assert message is not None
    reply_message = (
        db_session.query(Message)
        .filter_by(msg_id=234567890, to_id=openid)
        .first())
    assert reply_message is not None


def test_handler_user(handler, db_session, client, openid):
    left = handler.user
    right = client.get_user(openid)
    assert left == right
    user = db_session.query(User).filter_by(openid=openid).first()
    assert user == client.get_user(openid)


def test_location_reported(handler, db_session):
    assert handler.user_location.latitude == 39.1353
    assert handler.user_location.longitude == 117.518
    assert handler.user_location.precision == 30

    location = (
        db_session.query(Location)
        .filter_by(openid=handler.openid)
        .order_by(Location.create_time.desc()).first())
    assert location.latitude == 39.1353
    assert location.longitude == 117.518
    assert location.precision == 30

def test_refresh_user(xml_builder, db_session, DB_Session,
                          client, openid, monkeypatch):
    user =db_session.query(User).filter_by(openid=openid).first()
    assert user is not None

    old_time_func = time.time

    def mock_time():
        return old_time_func() + 86400

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

    assert user.nickname != info["nickname"]

    def mock_api_return(resp):
        return info

    monkeypatch.setattr(time, "time", mock_time)
    monkeypatch.setattr(requests.Response, "json", mock_api_return)

    xml_text = xml_builder(
        "text", "<Content><![CDATA[this is a test]]></Content>",
        msg_id=1234567890123456)
    handler = PersistMessageHandler(
        xml_text, client, db_session_maker=DB_Session,
        debug_to_wechat=True)
    handler.reply()

    assert handler.user.openid == info["openid"]
    assert handler.user.nickname == info["nickname"]
    assert handler.user.headimgurl == info["headimgurl"]