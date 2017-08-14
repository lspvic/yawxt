# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import time
import xml.etree.ElementTree as ET

__all__ = ["Message", "User", "Location"]

def pop_from_etree(xml, tag):
    ele = xml.find(tag)
    if ele is not None:
        xml.remove(ele)
        return ele
    return None

class Message(object):
    '''微信消息类，包括接收消息和发送消息，事件也属于消息
    
    :ivar to_user_id: 如果是接收的用户消息，则为公众号appid，
        如果是发送给用户的消息，则为用户openid
    :ivar from_user_id:  如果是接收的用户消息，则为用户openid，
        如果是发送给用户的消息，则为公众号appid
    :ivar create_time: 消息的创建时间，整型unix时间戳
    :ivar msg_type: 消息的类型，如 text, voice, 事件消息类型为event_加事件类型，如
        event_LOCATION, event_VIEW
    :ivar content: 消息除去头部自动构成的xml字符串，例如：
        
        .. code-block:: xml
        
            <Location_X>39.915119</Location_X>
            <Location_Y>116.403963</Location_Y>
            <Scale>16</Scale>
            <Label><![CDATA[北京市东城区东长安街]]></Label>
        
    '''
    __availabe_keys__ = ["to_user_id", "from_user_id", "create_time", "msg_id", "msg_type", "content"]
    
    def __init__(self, to_user_id, from_user_id, msg_id, msg_type, content, create_time=None):
        self.to_user_id = to_user_id
        self.from_user_id = from_user_id
        self.msg_id = msg_id
        self.msg_type = msg_type
        self.content = content
        self.create_time = create_time or int(time.time())
    
    def __repr__(self):
        return "Message(from=%s, to=%s, type=%s, id=%s" % (self.from_user_id, self.to_user_id, self.msg_type, self.msg_id)
        
    @classmethod
    def from_string(cls, content):
        '''从文本字符串构造 :class:`Message` 对象
        
        :param content: xml文本字符串
        :rtype:  Message
        '''
        if not isinstance(content, bytes):
            content = content.encode("utf8")
        xml = ET.fromstring(content)
        to_user_id = pop_from_etree(xml, 'ToUserName').text
        from_user_id = pop_from_etree(xml,
            'FromUserName').text
        msg_type = pop_from_etree(xml, 'MsgType').text
        if msg_type == "event":
            sub_type = pop_from_etree(xml, 'Event').text
            msg_type = "event_%s" % sub_type
        create_time = int(pop_from_etree(xml, 'CreateTime').text)
        msg_id_node = pop_from_etree(xml, 'MsgId')
        if msg_id_node is not None:
            msg_id = int(msg_id_node.text)
        else:
            msg_id = None
        return cls(to_user_id, from_user_id, msg_id, msg_type, ET.tostring(xml).decode(), create_time=create_time)
    
    def build_xml(self):
        '''生成此消息的xml字符
        
        :returns: 此消息对应的微信xml格式消息字符串
        :rtype: str
        '''
        texts = ['''<xml>
<ToUserName><![CDATA[%s]]></ToUserName>
<FromUserName><![CDATA[%s]]></FromUserName>
<CreateTime>%s</CreateTime>''' % (self.to_user_id, 
        self.from_user_id, self.create_time)]
        
        if self.msg_type.startswith("event_"):
            msg_type = "event"
            sub_type = self.msg_type[6:]
            texts.append('''<MsgType><![CDATA[%s]]></MsgType>
<Event><![CDATA[%s]]></Event>''' % (msg_type, sub_type))
        else:
            texts.append('''<MsgType><![CDATA[%s]]></MsgType>''' % self.msg_type)

        if self.msg_id is not None:
            texts.append("<MsgId>%s</MsgId>" % self.msg_id)
        texts.append(self.content)
        texts.append("</xml>")
        return "\n".join(texts)
    
class User(object):
    '''公众号用户类
    
    :ivar subscribe: 是否订阅该公众号
    :ivar openid: 用户的标识
    :ivar nickname: 用户的昵称
    :ivar sex: 用户的性别，值为1时是男性，值为2时是女性，
        值为0时是未知
    :ivar city: 用户所在城市
    :ivar country: 用户所在国家
    :ivar province: 用户所在省份    
    :ivar language: 用户的语言，简体中文为zh_CN
    :ivar headimgurl: 用户头像，最后一个数值代表正方形头像大小（有0、46、64、
        96、132数值可选，0代表640*640正方形头像），用户没有头像时该项为空。
        若用户更换头像，原有头像URL将失效。
    :ivar subscribe_time: 用户关注时间，为时间戳
    :ivar union: 只有在用户将公众号绑定到微信开放平台帐号后，才会出现该字段
    :ivar remark: 公众号运营者对粉丝的备注
    :ivar groupid: 用户所在的分组ID
    :ivar tagid_list: 用户被打上的标签ID列表，是逗号分割的字符串
    '''
    __availabe_keys__ = ["subscribe", "openid", "nickname", "sex", "city",
        "country", "province", "city", "headimgurl", "subscribe_time",
        "unionid", "remark", "groupid", "tagid_list", "language"
    ]
    
    def __init__(self, **kwargs):
        for key in self.__availabe_keys__:
            if key in kwargs:
                setattr(self, key, kwargs[key])
            else:
                setattr(self, key, None)
    
    @property
    def tagids(self):
        '''类型为整型list的tag id，如 ``[1,2,3]`` , 对应的tagid_list为 `'1,2,3'`'''
        return list(map(int, self.tagid_list.split(","))) if self.tagid_list else []
    
    def __repr__(self):
        return "User(openid=%s, nickname=%s)" % (self.openid, self.nickname)
        
    @classmethod
    def from_dict(cls, user_dict):
        '''从字典构造此类
        
        :param user_dict: 包含用户信息的字典对象
        :rtype: Message
        '''
        user_dict["tagid_list"] =  ",".join(map(str, user_dict["tagid_list"] if "tagid_list" in user_dict else []))
        user = cls(**dict((k, user_dict[k]) for k in user_dict if k in cls.__availabe_keys__))
        return user

    def to_dict(self):
        '''生成字典类型
        
        :rtype: dict
        '''
        val = dict((key, getattr(self, key)) for key in self.__availabe_keys__)
        val["tagid_list"] = self.tagids
        return val
        
    def update(self, update_dict):
        '''从字典信息更新此类字段
        
        :param update_dict: 包含用户信息的字典对象
        '''
        update_dict["tagid_list"] =  ",".join(map(str, update_dict["tagid_list"] if "tagid_list" in update_dict else []))
        for k in update_dict:
            if k in self.__availabe_keys__:
                setattr(self, k, update_dict[k])
                
class Location(object):
    '''用户上报地址类
    
    :ivar latitude: 位置纬度
    :ivar longitude: 位置经度
    :ivar precision: 位置精确度
    :ivar openid: 在次位置的用户openid
    :ivar time:  用户在此位置的时间
    '''
    __availabe_keys__ = ["latitude", "longitude", "precision", "openid", "time"]
    
    def __init__(self, latitude, longitude, precision, openid=None, location_time=None):
        self.latitude = latitude
        self.longitude = longitude
        self.precision = precision
        self.openid = openid
        self.time = location_time or time.time()
        
    def __repr__(self):
        return "Location(openid=%s, latitude=%s, longitude=%s" % (self.openid, self.latitude, self.longitude)
