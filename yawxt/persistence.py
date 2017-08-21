# -*- coding:utf-8 -*-

from __future__ import unicode_literals
import time
import logging

try:
    from sqlalchemy import (
        Table, Text, Column, Integer, String, Float, BigInteger)
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import mapper
except:
    logging.error(
        "please install sqlalchemy"
        "if you want to store wechat messages on database")
    raise

from .message import MessageHandler
from .models import User, Location, Message

__all__ = [
    "user_table", "message_table", "location_table",
    "create_all", "PersistMessageHandler"]

Base = declarative_base()

message_table = Table(
    "wechat_message", Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('to_id', String(100)),
    Column("from_id", String(100)),
    Column("msg_id", BigInteger),
    Column("msg_type", String(50)),
    Column("create_time", Integer),
    Column("content", Text),
)

user_table = Table(
    "wechat_user", Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("subscribe", Integer),
    Column("openid", String(100)),
    Column("nickname", String(50)),
    Column("sex", Integer),
    Column("city", String(40)),
    Column("country", String(40)),
    Column("province", String(40)),
    Column("language", String(40)),
    Column("headimgurl", String(512)),
    Column("subscribe_time", Integer),
    Column("unionid", String(100), unique=True),
    Column("remark", String(100)),
    Column("groupid", Integer),
    Column("tagid_list", String(100)),
    Column("update_time", Integer, default=lambda: int(time.time()))
)

location_table = Table(
    "wechat_location", Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("precision", Float),
    Column("create_time", Integer, default=lambda: int(time.time())),
    Column("openid", String(100)),
)

mapper(
    Message, message_table,
    properties=dict(
        (key, getattr(message_table.c, key))
        for key in Message.__availabe_keys__)
)

mapper(
    User, user_table,
    properties=dict(
        (key, getattr(user_table.c, key))
        for key in User.__availabe_keys__)
)

mapper(
    Location, location_table,
    properties=dict(
        (key, getattr(location_table.c, key))
        for key in Location.__availabe_keys__)
)


def create_all(bind):
    '''创建数据库及所有表

    :param bind: 一般为sqlalchemy ``Engine`` 对象
    '''
    Base.metadata.create_all(bind)


class PersistMessageHandler(MessageHandler):
    '''消息持久化类，继承此类自动将每一条消息、地理位置上报、
        发送消息用户资料保存到数据库

    :param content: 微信发送的消息xml字符串
    :param client: 微信公众号账号, :class:`~yawxt.WxClient` 对象
    :param db_session_maker: sqlalchemy session生成方法，一般为
        ``sessionmaker(bind=engine)`` ，例如

        .. code-block:: python

            Session = sessionmaker(bind=engine)
            processor = PersistMessageHandler(content, client,
                db_session_maker = Session)

    '''

    def __init__(self, content, client,  db_session_maker, **kwargs):
        self.db_session = db_session_maker()
        self._user_location = None
        self._refresh_interval = kwargs.pop("user_refresh_days", 1)
        super(PersistMessageHandler, self).__init__(content, client, **kwargs)

    @property
    def user_location(self):
        '''用户的地理位置，用户最后一次上报的位置，从数据库中获取

        :type: :class:`~yawxt.Location`
        '''
        if not self._user_location:
            self._user_location = (
                self.db_session.query(Location)
                .filter_by(openid=self.openid)
                .order_by(Location.create_time.desc())
                .first())
            self.log("find user's location: %s" % self._user_location)
        return self._user_location

    def _before(self):
        self.save_user_info()
        self.db_session.add(self.message)
        self.before()

    def _subscribe(self):
        self.save_user_info(refresh_interval=0)
        ele = self.xml.find("EventKey")
        # 当不是扫码关注时，EventKey存在但内容为空
        if ele is not None and ele.text:
            # event_key一定是以 "qrscene_" 开头的
            event_key = int(ele.text[8:])
            ticket = self.xml.find("Ticket").text
            self.event_subscribe_from_qrcode(event_key, ticket)
        else:
            self.event_subscribe()

    def _unsubscribe(self):
        self.save_user_info(refresh_interval=0)
        self.event_unsubscribe()

    def _LOCATION(self):
        lat = float(self.xml.find('Latitude').text)
        lon = float(self.xml.find('Longitude').text)
        precision = float(self.xml.find('Precision').text)
        location = Location(
            lat, lon, precision, self.openid,
            self.message.create_time)
        self.db_session.add(location)
        self.log("add location to db: %s" % location)
        self._user_location = location
        self.event_location(location)

    def save_user_info(self, refresh_interval=None):
        '''保存或更新发送消息的用户的信息

        :param refresh_interval: 从微信服务器刷新用户信息的间隔时间，从上次
            保存到数据库到现在超过时间间隔则从微信数据库拉取，单位为天，
            可以使用小数，默认为1天, refresh_interval为0时一直拉取.

        '''
        if refresh_interval is None:
            refresh_interval = self._refresh_interval

        user = (self.db_session.query(User)
                .filter_by(openid=self.openid).first())
        self.log("find user in db: %s" % user)
        refresh = (
            user is not None and
            (time.time() - user.update_time) > refresh_interval * 86400 - 3
        )
        if refresh or user is None:
            _user = self.client.get_user(self.openid)
            if user is None:
                user = _user
                self.db_session.add(user)
                self.log("add user to db with dict: %s" % user)
            else:
                user.update(_user)
                user.update_time = int(time.time())
                self.log("update user with dict: %s" % _user)
        self._user = user

    def _finish(self):
        self.finish()

        entities = [self.message, self._user]
        if self.reply_message is not None:
            self.db_session.add(self.reply_message)
            entities.append(self.reply_message)

        self.db_session.commit()
        for entity in entities:
            self.db_session.refresh(entity)
        self.db_session.close()
