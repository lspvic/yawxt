# -*- coding: utf-8 -*-

import time
import random
import string
import hashlib

import pytest
from yawxt import *
from yawxt.persistence import create_all

from flask_wechat import app, db, token
import flask_wechat

@pytest.fixture(scope="session", autouse=True)
def create_db():
    create_all(db.engine)
    
@pytest.fixture(scope="session", autouse=True)
def inject_account(account):
    flask_wechat.wechat_account = account

@pytest.fixture(scope="module")
def client():
    return app.test_client()
    
@pytest.fixture(scope="function")
def args():
    timestamp = str(int(time.time()))
    nonce = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))
    tmpArr = sorted([token, timestamp, nonce])
    tmpStr = ''.join(tmpArr)
    signature = hashlib.sha1(tmpStr.encode()).hexdigest()
    args = {"timestamp": timestamp, "nonce": nonce, "signature": signature}
    return args
    
def test_args(client):
    rv = client.get("/wechat")
    assert b"Messages not From Wechat" == rv.data
    
def test_echostr(client, args):
    echostr = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))
    args["echostr"] = echostr
    rv = client.get("/wechat", query_string=args)
    assert rv.get_data(as_text=True) == echostr
    
def test_message(client, args, openid, account, xml_builder):
    data = xml_builder("event_LOCATION", '''
<Latitude>39.120232</Latitude>
<Longitude>117.529915</Longitude>
<Precision>40.0</Precision>''')
    rv = client.post("/wechat", query_string=args, data=data)
    location = db.session.query(Location).filter_by(openid=openid).order_by(Location.time.desc()).first()
    assert location.latitude == 39.120232
    assert location.longitude == 117.529915
    assert location.precision == 40.0
    msg_count = db.session.query(Message).count()
    assert msg_count >= 2
    user = db.session.query(User).filter_by(openid=openid).first()
    assert user is not None
    message = Message.from_string(rv.data)
    assert message.msg_type == "text"
    assert message.to_user_id == openid
    assert message.from_user_id == account.appid
    assert "39.120232" in message.content
    assert "117.529915" in message.content
    
def test_video_message(client, args, openid, account, xml_builder):
    data = xml_builder("video", '''<MediaId><![CDATA[gad4123fasf321]]></MediaId>
<ThumbMediaId><![CDATA[thumb_media_id]]></ThumbMediaId>
''', 1234567890123456)
    rv = client.post("/wechat", query_string=args, data=data)
    message = Message.from_string(rv.data)
    assert message.msg_type == "video"
    assert message.to_user_id == openid
    assert message.from_user_id == account.appid
    assert "gad4123fasf321" in message.content