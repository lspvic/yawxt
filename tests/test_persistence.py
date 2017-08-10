# -*- coding: utf-8 -*-

import time

import pytest

from yawxt.persistence import PersistentMessageProcessor, create_all
from yawxt.models import *

@pytest.fixture(autouse=True)
def processor(account, DB_Session, xml_builder):
    xml_text = xml_builder("text", "<Content><![CDATA[this is a test]]></Content>", 
        msg_id=1234567890123456)
    processor = PersistentMessageProcessor(xml_text, account, 
        db_session_maker = DB_Session, debug_to_wechat = True)
    processor.reply()
    return processor

def test_message_save(account, xml_builder, DB_Session, db_session, openid):
    xml_text = xml_builder("text", "<Content><![CDATA[this is a test]]></Content>", 
        msg_id=234567890)
    processor = PersistentMessageProcessor(xml_text, account, 
        db_session_maker = DB_Session, debug_to_wechat = True)
    processor.reply()
    message = db_session.query(Message).filter_by(msg_id=234567890, from_user_id=openid).first()
    assert message is not None
    reply_message = db_session.query(Message).filter_by(msg_id=234567890, to_user_id=openid).first()
    assert reply_message is not None
    
def test_user(processor, db_session, account, openid):
    assert processor.user.to_dict() == account.get_user_info(openid).to_dict()
    user = db_session.query(User).filter_by(openid=openid).first()
    assert user.to_dict() == account.get_user_info(openid).to_dict()
    
def test_location_reported(processor, db_session):
    assert processor.user_location.latitude == 39.1353
    assert processor.user_location.longitude == 117.518
    assert processor.user_location.precision == 30
    
    location = db_session.query(Location).filter_by(openid=processor.openid).order_by(Location.time.desc()).first()
    assert location.latitude == 39.1353
    assert location.longitude == 117.518
    assert location.precision == 30