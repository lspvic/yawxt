# -*- coding: utf-8 -*-
import time
import xml.etree.ElementTree as ET

__all__ = ["Message", "User", "Location"]

def pop_from_etree(xml, tag):
    ele = xml.find(tag)
    if ele is not None:
        xml.remove(ele)
        return ele
    return None

class Message:
    '''微信消息类，包括接收消息和发送消息，事件也属于消息
    
    :ivar to_user_id: 消息发送方的id，如果为用户则是用户openid，如果为公众号，则是公众号appid
    :ivar from_user_id: 消息接收方的id，如果为用户则是用户openid，如果为公众号，则是公众号appid
    :ivar create_time: 消息的创建时间，unix时间戳，整型
    :ivar msg_type: 消息的类型，如 text, voice, event等
    :ivar content: 消息除去头部自动构成的xml字符串
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
        return cls(to_user_id, from_user_id, msg_id, msg_type, ET.tostring(xml, encoding="unicode"), create_time=create_time)
    
    def build_xml(self):
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
    
class User:
    '''公众号用户类
    
    :ivar subscribe:
    :ivar openid:
    :ivar nickname:
    :ivar sex:
    :ivar city:
    :ivar country:
    :ivar province:
    :ivar headimgurl:
    :ivar subscribe_time:
    :ivar union:
    :ivar remark:
    :ivar groupid:
    :ivar tagid_list:
    :ivar language:
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
        return list(map(int, self.tagid_list.split(","))) if self.tagid_list else []
    
    def __repr__(self):
        return "User(openid=%s, nickname=%s)" % (self.openid, self.nickname)
        
    @classmethod
    def from_dict(cls, user_dict):
        user_dict["tagid_list"] =  ",".join(map(str, user_dict["tagid_list"] if "tagid_list" in user_dict else []))
        user = cls(**{k:user_dict[k] for k in user_dict if k in cls.__availabe_keys__})
        return user

    def to_dict(self):
        val = {key: getattr(self, key) for key in self.__availabe_keys__}
        val["tagid_list"] = self.tagids
        return val
        
    def update(self, update_dict):
        update_dict["tagid_list"] =  ",".join(map(str, update_dict["tagid_list"] if "tagid_list" in update_dict else []))
        for k in update_dict:
            if k in self.__availabe_keys__:
                setattr(self, k, update_dict[k])
        self.update_time = int(time.time())
                
class Location:
    '''用户上报地址类
    
    :ivar latitude:
    :ivar longitude:
    :ivar precision:
    :ivar openid:
    :ivar time:
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
