# -*- coding: utf-8 -*-

import time
import random
import string
import hashlib

import pytest
from yawxt import Message, User, Location
from yawxt.persistence import create_all

from flask_wechat import app, db, token
import flask_wechat


@pytest.fixture(scope="session", autouse=True)
def create_db(tmpdir_factory):
    path = 'sqlite:///%s' % (
        tmpdir_factory.mktemp("flask").join("wechat.db").realpath())
    flask_wechat.app.config["SQLALCHEMY_DATABASE_URI"] = path
    db.init_app(app)
    create_all(db.engine)


@pytest.fixture(scope="session", autouse=True)
def inject_account(client):
    flask_wechat.wechat_account = client


@pytest.fixture(scope="module")
def app_client():
    return app.test_client()


@pytest.fixture(scope="function")
def args():
    timestamp = str(int(time.time()))
    nonce = ''.join(random.choice(
        string.ascii_letters + string.digits) for _ in range(15))
    tmpArr = sorted([token, timestamp, nonce])
    tmpStr = ''.join(tmpArr)
    signature = hashlib.sha1(tmpStr.encode()).hexdigest()
    args = {"timestamp": timestamp, "nonce": nonce, "signature": signature}
    return args


def test_args(app_client):
    rv = app_client.get("/wechat")
    assert b"Messages not From Wechat" == rv.data


def test_echostr(app_client, args):
    echostr = ''.join(
        random.choice(string.ascii_letters + string.digits) for _ in range(15))
    args["echostr"] = echostr
    rv = app_client.get("/wechat", query_string=args)
    assert rv.get_data(as_text=True) == echostr


def test_message(app_client, args, openid, client, xml_builder):
    data = xml_builder("event_LOCATION", '''
<Latitude>39.120232</Latitude>
<Longitude>117.529915</Longitude>
<Precision>40.0</Precision>''')
    rv = app_client.post("/wechat", query_string=args, data=data)
    location = (
        db.session.query(Location)
        .filter_by(openid=openid)
        .order_by(Location.create_time.desc()).first())
    assert location.latitude == 39.120232
    assert location.longitude == 117.529915
    assert location.precision == 40.0
    msg_count = db.session.query(Message).count()
    assert msg_count >= 2
    user = db.session.query(User).filter_by(openid=openid).first()
    assert user is not None
    message = Message.from_string(rv.data)
    assert message.msg_type == "text"
    assert message.to_id == openid
    assert message.from_id == client.appid
    assert "39.120232" in message.content
    assert "117.529915" in message.content


def test_video_message(app_client, args, openid, client, xml_builder):
    data = xml_builder(
        "video", '''<MediaId><![CDATA[gad4123fasf321]]></MediaId>
<ThumbMediaId><![CDATA[thumb_media_id]]></ThumbMediaId>
''', 1234567890123456)
    rv = app_client.post("/wechat", query_string=args, data=data)
    message = Message.from_string(rv.data)
    assert message.msg_type == "video"
    assert message.to_id == openid
    assert message.from_id == client.appid
    assert "gad4123fasf321" in message.content
