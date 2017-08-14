# -*- coding:utf-8 -*-

import time
import logging

try:
    from sqlalchemy import Table, Text, Column, Integer, String, Float, ForeignKey, BigInteger
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import mapper
except:
    logging.error("please install sqlalchemy if you want to store wechat messages on database")
    raise

from .message import MessageProcessor
from .models import *

__all__ = ["user_table", "message_table", "location_table", "create_all", "PersistentMessageProcessor"]
    
Base = declarative_base()

message_table = Table("message", Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('to_user_id', String(100)),
    Column("from_user_id", String(100)),
    Column("msg_id", BigInteger),
    Column("msg_type", String(50)),
    Column("create_time", Integer),
    Column("content", Text),
)

user_table = Table("user", Base.metadata,
    Column("id", Integer, primary_key = True),
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
    Column("unionid", String(100), unique = True),
    Column("remark", String(100)),
    Column("groupid", Integer),
    Column("tagid_list", String(100)),
    Column("update_time", Integer, default = lambda :int(time.time()))
)

location_table = Table("location", Base.metadata, 
    Column("id", Integer, primary_key = True),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("precision", Float),
    Column("time", Integer, default = lambda:int(time.time())),
    Column("openid", String(100)),
)

mapper(Message, message_table,
    properties={key: getattr(message_table.c, key) for key in Message.__availabe_keys__}
)
    
mapper(User, user_table,
    properties={key: getattr(user_table.c, key) for key in User.__availabe_keys__}
)

mapper(Location, location_table,
    properties={key: getattr(location_table.c, key) for key in Location.__availabe_keys__}
)

def create_all(bind):
    '''创建数据库及所有表
    
    :param bind: 一般为sqlalchemy ``Engine`` 对象
    '''
    Base.metadata.create_all(bind) 
       
class PersistentMessageProcessor(MessageProcessor):
    '''消息持久化类，继承此类自动将每一条消息、地理位置上报、
        发送消息用户资料保存到数据库
        
    :param content: 微信发送的消息xml字符串
    :param account: 微信公众号账号, :class:`~yawxt.OfficialAccount` 对象
    :param db_session_maker: sqlalchemy session生成方法，一般为
        ``sessionmaker(bind=engine)`` ，例如
        
        .. code-block:: python
        
            Session = sessionmaker(bind=engine)
            processor = PersistentMessageProcessor(content, account,
                db_session_maker = Session)

    '''
        
    def __init__(self, content, account,  db_session_maker, **kwargs):
        self.db_session = db_session_maker(expire_on_commit=False)
        self._user_location = None
        super(PersistentMessageProcessor, self).__init__(content, account, **kwargs)
    
    @property
    def user_location(self):
        '''用户的地理位置，用户最后一次上报的位置，从数据库中获取
        
        :type: :class:`~yawxt.Location`
        '''
        if not self._user_location:
            self._user_location = self.db_session.query(Location).filter_by(openid=self.openid).order_by(Location.time.desc()).first()
            self.log("find user's location: %s" % self._user_location)
        return self._user_location
        
    def before(self):
        self.save_user_info()
        self.db_session.add(self.message)
        super(PersistentMessageProcessor, self).before()
    
    def event_location(self, location):
        self.db_session.add(location)
        self.log("add location to db: %s" % location)
        self._user_location = location
        super(PersistentMessageProcessor, self).event_location(location)
    
    def save_user_info(self, force_update = False):
        '''保存或更新发送消息的用户的信息
        
        :param force_update: 强制从微信服务器获取用户最新资料，默认为 `False` .
        '''
        user = self.db_session.query(User).filter_by(openid=self.openid).first()
        self.log("find user in db: %s" % user)
        if force_update or user is None:
            print("GET USER INFO")
            info = self.account.get_user_info(self.openid)
            if user is None:
                user = info
                self.db_session.add(user)
                self.log("add user to db with dict: %s" % user)
            else:
                user.update(info.to_dict())
                self.log("update user with dict: %s" % info)
        self._user = user
        
    def finish(self):    
        super(PersistentMessageProcessor, self).finish()
        
        if self.reply_message is not None:
            self.db_session.add(self.reply_message)
            
        self.db_session.commit()
        self.db_session.close()
        