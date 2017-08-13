# -*- coding: utf-8 -*-

'''Tests for Message Recieve'''

import os
import time
import random
import hashlib
import string
import xml.etree.ElementTree as ET

import pytest
from flask import Flask, request
from yawxt import OfficialAccount, MessageProcessor, check_signature, Message

class MessageProcessorTester(MessageProcessor):

    def __init__(self, content, state = None, debug_to_wechat = None):
        self.state = None
        super(MessageProcessorTester, self).__init__(content, debug_to_wechat = debug_to_wechat)
    
    def event_location(self, location):
        #  assert latitude == 23.1374665
        #  assert longitude == 113.352425
        #  assert precision == 119.385040
        self.state = (location.latitude, location.longitude, location.precision)
        
    def event_unsubscribe(self):
        self.state = "unsubscribe"
        
    def event_subscribe(self, scene_value = None, ticket = None):
        if scene_value is None:
            self.state = "欢迎您订阅公众号"
        else:
            self.state = (scene_value, ticket)
    
    def event_view(self, view_key):
        self.state = "open url %s" % view_key
        
    def event_click(self, click_key):
        self.state = "pull %s" % click_key
        
    def event_scan(self, scene_value, ticket):
        self.state = "scan %s, get %s" % (scene_value, ticket)
        
    def event_template_send_job_finished(self, status):
        self.state = "template send with %s" %  status
        
    def on_text(self, text):
        self.state = text
        self.reply_text(text)
        
    def on_image(self, media_id, pic_url):
        self.state  = pic_url, media_id
        self.reply_image(media_id)
        
    def on_voice(self, media_id, format, recognition):
        self.state = (media_id, format, recognition)
        self.reply_voice(media_id)
        
    def on_video(self, media_id, thumb_id):
        self.state = (media_id, thumb_id)
        self.reply_video(media_id, "video title")

    def on_shortvideo(self, media_id, thumb_id):
        self.state = (media_id, thumb_id)
        self.reply_music(media_id, title="music title",
                    description="music description", 
                    url="http://qq.com", hqurl="http://qq.com")
        
    def on_location(self, x, y, scale, label):
        self.state = (x, y, scale, label)
        article = {"title": "news title", 
            "description": "news description", 
            "picurl": "http://qq.com",
            "url": "http://qq.com"
        }
        self.reply_news([article for _ in range(5)])

    def on_link(self, url, title, desc):
        self.state = (title, desc, url)

parameters = {
    "location": (("event_LOCATION", '''<Latitude>23.137466</Latitude>
<Longitude>113.352425</Longitude>
<Precision>119.385040</Precision>'''), 
    (23.137466, 113.352425, 119.385040)),
    "subscribe": (("event_subscribe", ""),
        "欢迎您订阅公众号"),
    "subscribe_qrcode": (("event_subscribe", '''
<EventKey><![CDATA[qrscene_123123]]></EventKey>
<Ticket><![CDATA[TICKET]]></Ticket>'''),
        (123123, "TICKET")),
    "unsubscribe": (("event_unsubscribe", ""),
        "unsubscribe"),
    "view": (("event_VIEW", '''
<EventKey><![CDATA[www.qq.com]]></EventKey>
'''), "open url www.qq.com"),
    "click":(("event_CLICK", '''
<EventKey><![CDATA[134j34;ioafs]]></EventKey>
'''),"pull 134j34;ioafs"),
    "scan": (("event_SCAN", '''
<EventKey><![CDATA[324134]]></EventKey>
<Ticket><![CDATA[ticket_fa]]></Ticket>
'''), "scan 324134, get ticket_fa"),
    "template_send": (("event_TEMPLATESENDJOBFINISH",
        '''<MsgID>200163836</MsgID>
           <Status><![CDATA[success]]></Status>'''),
           "template send with success"),
    "text":(("text", '''<Content><![CDATA[this is a test]]></Content>
''', 1234567890123456), 'this is a test'),
    "image": (("image", '''<PicUrl><![CDATA[this is a url]]></PicUrl>
 <MediaId><![CDATA[media_id]]></MediaId>
''', 1234567890123456), ("this is a url", "media_id")),
    "voice": (("voice", '''
<MediaId><![CDATA[media_id]]></MediaId>
<Format><![CDATA[Format]]></Format>
<Recognition><![CDATA[腾讯微信团队]]></Recognition>
''', 1234567890123456), ("media_id", "Format", "腾讯微信团队")),
    "video": (("video", '''
<MediaId><![CDATA[media_id]]></MediaId>
<ThumbMediaId><![CDATA[thumb_media_id]]></ThumbMediaId>
''', 1234567890123456), ("media_id", "thumb_media_id")),
    "shortvideo": (("shortvideo", '''
<MediaId><![CDATA[media_id]]></MediaId>
<ThumbMediaId><![CDATA[thumb_media_id]]></ThumbMediaId>
''', 1234567890123456), ("media_id", "thumb_media_id")),
    "location_msg": (("location", '''
<Location_X>23.134521</Location_X>
<Location_Y>113.358803</Location_Y>
<Scale>20</Scale>
<Label><![CDATA[位置信息]]></Label>
''', 1234567890123456), (23.134521, 113.358803, 20, "位置信息")),
    "link": (("link", '''
<Title><![CDATA[公众平台官网链接]]></Title>
<Description><![CDATA[公众平台官网链接]]></Description>
<Url><![CDATA[url]]></Url>''', 1234567890123456), 
    ("公众平台官网链接", "公众平台官网链接", "url")),
}

@pytest.fixture(scope="module", params=parameters.values(), ids=list(parameters.keys()))
def parametrize(request):
    return request.param
    
def test_event(parametrize, xml_builder):
    content, expected = parametrize
    print(xml_builder(*content))
    processor = MessageProcessorTester(xml_builder(*content), debug_to_wechat=True)
    assert processor.state == expected

@pytest.mark.parametrize("token,nonce,timestamp,signature, time_error",
    [("LpxhtFU4GN", "awekRO2Q2rhIXv3N5WUK", "1502593490", "22c3c573b9e4c3a15735a2f077bef067f4aac8d6", 0),
    pytest.param("LpxhtFU4GN", "awekRO2Q2rhIXv3N5WUK", "1502593490", "22c3c573b9e4c3a15735a2f077bef067f4aac8d6", 600, marks=pytest.mark.xfail),
    pytest.param("LpxhtFU4Gn", "awekRO2Q2rhIXv3N5WUK", "1502593490", "22c3c573b9e4c3a15735a2f077bef067f4aac8d6", 0, marks=pytest.mark.xfail),
    pytest.param("LpxhtFU4GN", "awekRO2Q2rhIXv3N5WUK", "1502593490", "22c3c573b9e4c3a15735a2f077bef067f4aac8d5", 0, marks=pytest.mark.xfail),
    ])
def test_check_signature(token, nonce, timestamp, signature, time_error):
    assert check_signature(token, nonce, timestamp, signature, time_error=time_error)
    
def test_processor_property(xml_builder, openid):
    data = xml_builder(*parameters["text"][0])
    processor = MessageProcessorTester(data, debug_to_wechat=True)
    assert processor.openid == openid
    assert processor.user is None
    
def test_process_message(xml_builder):
    data = xml_builder(*parameters["text"][0])
    processor = MessageProcessorTester(data, debug_to_wechat=True)
    from_message = processor.message
    assert from_message.msg_id == 1234567890123456
    assert from_message.msg_type == "text"
    assert from_message.create_time > 1348831860
    assert from_message.create_time < time.time()
    assert "<Content>this is a test</Content>" in from_message.content    
    
    reply_message = Message.from_string(processor.reply())
    assert from_message.from_user_id == reply_message.to_user_id
    assert from_message.to_user_id == reply_message.from_user_id
    
def test_reply_text(xml_builder, account, openid):
    data = xml_builder(*parameters["text"][0])
    processor = MessageProcessorTester(data, debug_to_wechat=True)
    xml_str = processor.reply()
    message = Message.from_string(xml_str)
    
    ## 测试发送给微信服务器的消息的头部是正确的
    xml = ET.fromstring(xml_str)
    assert xml.find("ToUserName").text == message.to_user_id
    assert xml.find("FromUserName").text == message.from_user_id
    assert int(xml.find("CreateTime").text) == message.create_time
    assert xml.find("MsgType").text == message.msg_type
    assert xml.find("Content").text == ET.fromstring(message.content).find("Content").text
    
    ## 测试Message类的属性是正确的
    assert message.from_user_id == account.appid
    assert message.to_user_id == openid
    assert message.msg_type == 'text'
    assert isinstance(message.create_time, int)
    assert ET.fromstring(message.content).find("Content").text == "this is a test"
    
def test_reply_image(xml_builder):
    data = xml_builder(*parameters["image"][0] )
    processor = MessageProcessorTester(data, debug_to_wechat=True)
    message = Message.from_string(processor.reply())
    assert message.msg_type == "image"
    assert ET.fromstring(message.content).find("Image").find("MediaId").text == "media_id"
    
def test_reply_voice(xml_builder):
    data = xml_builder(*parameters["voice"][0])
    processor = MessageProcessorTester(data, debug_to_wechat=True)
    message = Message.from_string(processor.reply())
    assert message.msg_type == "voice"
    assert ET.fromstring(message.content).find("Voice").find("MediaId").text == "media_id"
    
def test_reply_video(xml_builder):
    data = xml_builder(*parameters["video"][0])
    processor = MessageProcessorTester(data, debug_to_wechat=True)
    message = Message.from_string(processor.reply())
    assert message.msg_type == "video"
    video_xml = ET.fromstring(message.content).find("Video")
    assert video_xml.find("MediaId").text == "media_id"
    assert video_xml.find("Title").text == "video title"
    assert video_xml.find("Description") is None
    
def test_reply_music(xml_builder):
    data = xml_builder(*parameters["shortvideo"][0])
    processor = MessageProcessorTester(data, debug_to_wechat=True)
    message = Message.from_string(processor.reply())
    assert message.msg_type == "music"
    video_xml = ET.fromstring(message.content).find("Music")
    assert video_xml.find("ThumbMediaId").text == "media_id"
    assert video_xml.find("Title").text == "music title"
    assert video_xml.find("Description").text == "music description"
    assert video_xml.find("MusicUrl").text == "http://qq.com"
    assert video_xml.find("HQMusicUrl").text == "http://qq.com"
    
def test_reply_news(xml_builder):
    data = xml_builder(*parameters["location_msg"][0])
    processor = MessageProcessorTester(data, debug_to_wechat=True)
    message = Message.from_string(processor.reply())
    assert message.msg_type == "news"
    assert ET.fromstring(message.content).find("ArticleCount").text == "5"
    video_xml = ET.fromstring(message.content).find("Articles").find("item")
    assert video_xml.find("Title").text == "news title"
    assert video_xml.find("Description").text == "news description"
    assert video_xml.find("PicUrl").text == "http://qq.com"
    assert video_xml.find("Url").text == "http://qq.com"