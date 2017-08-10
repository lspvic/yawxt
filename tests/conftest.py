# -*- coding: utf-8 -*-

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
def DB_Session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from yawxt.persistence import create_all

    engine = create_engine('sqlite:///data.db', echo=True)
    create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session
    
@pytest.fixture()
def db_session(DB_Session):
    s = DB_Session()
    yield s
    s.close()
    
@pytest.fixture(scope="session")
def xml_builder(account, openid):
    from yawxt import Message
    def func(msg_type, content, msg_id = None):
        return Message(account.appid, openid, msg_id, msg_type, 
            content).build_xml()
    return func
    
@pytest.fixture(scope="session", autouse=True)
def location_report(account, DB_Session, xml_builder):
    from yawxt.persistence import PersistentMessageProcessor
    locations = [(37.2356, 120.001, 40),
                       (38.1478, 118.456, 50),
                       (39.1353, 117.518, 30),]
    location_str = '''<Latitude>%s</Latitude>
<Longitude>%s</Longitude>
<Precision>%s</Precision>'''
    for loc in locations:
        msg_text = xml_builder("event_LOCATION", location_str % loc)
        processor = PersistentMessageProcessor(msg_text, 
            account, db_session_maker = DB_Session, 
            debug_to_wechat = True)
        processor.reply()
        time.sleep(2)