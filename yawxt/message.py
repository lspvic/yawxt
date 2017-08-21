# -*- coding:utf-8 -*-

from __future__ import unicode_literals
import time
import hashlib
import logging
import xml.etree.ElementTree as ET

__all__ = ["check_signature", "MessageHandler"]

from .models import Location, Message

logger = logging.getLogger(__name__)


def check_signature(token, timestamp, nonce, signature, time_error=600):
    '''微信消息的签名检查

    :param token: 公众号后台填写的token
    :param timestamp: 从发送消息url query_string获取的timestamp参数
    :param nonce: 从发送消息url query_string获取的nonce参数
    :param signature: 从发送消息url query_string获取的signature参数
    :param time_error: 时间误差，与微信服务器时间的误差允许秒数，
        设置为0表示不检查，默认为600秒
    '''
    if any(arg is None for arg in (token, timestamp, nonce, signature)):
        return False
    if time_error > 0 and abs(int(timestamp) - time.time()) > time_error:
        return False
    tmpArr = sorted([token, timestamp, nonce])
    tmpStr = ''.join(tmpArr)
    tmpStr = hashlib.sha1(tmpStr.encode()).hexdigest()
    return tmpStr == signature


class MessageHandler(object):
    '''微信消息处理基类，继承此类定义不同消息的处理函数

    #. 继承以 ``event_`` 开头的方法对event事件进行处理，这类消息一般不进行回复

    #. 继承以 ``on_``  开头的方法是对接收普通消息进行处理及回复消息

    #. 使用以 ``reply_`` 开头的方法进行回复内容，注意，多次调用此方法只会回复最后\
    一次调用的消息

    #. 使用 :meth:`reply` 得到最终发送给微信服务器的文本字符串

    :param content: 从微信服务器接收的xml格式的消息字符串
    :param client: 微信公众号账号, :class:`WxClient` 对象，
        默认为 ``None`` ，不设置
    :param debug_to_wechat: 使用 reply_debug_text 可以将调试信息发送到用户微信

    :ivar openid: 发送消息用户的openid
    :ivar message: 接收到的消息对象，类型为 :class:`yawxt.Message`
    '''

    def __init__(self, content, client=None,
                 debug_to_wechat=False):
        self.client = client
        self._debug_to_wechat = debug_to_wechat
        self._user = None

        self._reply = ''
        self._reply_type = None
        self._processed = False

        self.message = Message.from_string(content)
        self.reply_message = None
        self.openid = self.message.from_id
        self.log("message received %s, content: %s" % (
            self.message, self.message.content))
        self._before()

        self.xml = ET.fromstring(self.message.content)
        if self.message.msg_type.startswith('event_'):
            msg_type = self.message.msg_type[6:]
        else:
            msg_type = self.message.msg_type
        proc = getattr(self, "_%s" % msg_type, None)
        if proc is None:
            self.log("unkown type found: %s" % msg_type,
                     level=logging.WARNING)
        else:
            proc()

    @property
    def user(self):
        '''发送微信消息的用户信息，为 :class:`User` 对象，
            使用公众号 :class:`WxClient` API获取，如果 ``client`` 为 ``None`` ，
            则返回 ``None`` '''

        if self.client is not None and self._user is None:
            self._user = self.client.get_user(self.openid)
        return self._user

    def before(self):
        '''在处理具体消息内容之前调用，可以使用  :attr:`self.openid` , :attr:`self.user` ,

            :attr:`self.messsage` 等属性
        '''
        pass

    def log(self, content, level=logging.DEBUG, **kwargs):
        logger.log(
            level,
            "message openid(%s): %s",
            self.openid,
            content,
            **kwargs)

    def _before(self):
        self.before()

    def _finish(self):
        self.finish()

    def _subscribe(self):
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
        self.event_unsubscribe()

    def _LOCATION(self):
        lat = float(self.xml.find('Latitude').text)
        lon = float(self.xml.find('Longitude').text)
        precision = float(self.xml.find('Precision').text)
        location = Location(
            lat, lon, precision, self.openid,
            self.message.create_time)
        self.log("location event: %r" % location)
        self.event_location(location)

    def _CLICK(self):
        click_key = self.xml.find('EventKey').text
        self.log("click event: %s" % click_key)
        self.event_click(click_key)

    def _VIEW(self):
        view_key = self.xml.find('EventKey').text
        self.log("view event: %s" % view_key)
        self.event_view(view_key)

    def _SCAN(self):
        scene_value = int(self.xml.find("EventKey").text)
        ticket = self.xml.find("Ticket").text
        self.event_scan(scene_value, ticket)

    def _TEMPLATESENDJOBFINISH(self):
        status = self.xml.find("Status").text
        self.event_template_send_job_finished(status)

    def _text(self):
        text = self.xml.find('Content').text
        self.on_text(text)

    def _image(self):
        pic_url = self.xml.find('PicUrl').text
        media_id = self.xml.find('MediaId').text
        self.on_image(media_id, pic_url)

    def _voice(self):
        media_id = self.xml.find('MediaId').text
        voice_format = self.xml.find('Format').text
        recognition_element = self.xml.find('Recognition')
        if recognition_element is not None:
            recognition = recognition_element.text
        else:
            self.log("not set void to text, recognition is None")
            recognition = None
        self.on_voice(media_id, voice_format, recognition)

    def _video(self):
        media_id = self.xml.find('MediaId').text
        thumb_id = self.xml.find('ThumbMediaId').text
        self.on_video(media_id, thumb_id)

    def _shortvideo(self):
        media_id = self.xml.find('MediaId').text
        thumb_id = self.xml.find('ThumbMediaId').text
        self.on_shortvideo(media_id, thumb_id)

    def _location(self):
        x = float(self.xml.find('Location_X').text)
        y = float(self.xml.find('Location_Y').text)
        scale = float(self.xml.find('Scale').text)
        label = self.xml.find('Label').text
        self.on_location(x, y, scale, label)

    def _link(self):
        url = self.xml.find('Url').text
        title = self.xml.find('Title').text
        desc = self.xml.find('Description').text
        self.on_link(url, title, desc)

    def event_location(self, location):
        '''上报用户地理位置事件

        :param location: 地理位置 :class:`~yawxt.Location` 对象
        '''
        self.reply_debug_text(
            "location reported: %r" % location)

    def event_subscribe_from_qrcode(self, scene_value, ticket):
        '''用户扫码关注公众号事件

        :param scene_value: 扫码关注时的二维码场景值
        :param ticket: 扫码关注时的票据，如果只处理订阅事件，忽略这两个参数

        .. seealso:: :meth:`event_scan` , :meth:`event_subscribe` .
        '''
        self.reply_debug_text(
                '您扫码关注了公众号，scene_value: '
                '%s, ticket: %s' % (scene_value, ticket))

    def event_subscribe(self):
        '''用户关注公众号事件

        .. seealso:: :meth:`event_subscribe_from_qrcode`
        '''
        self.reply_text('欢迎您订阅我们的微信公众号')

    def event_unsubscribe(self):
        '''用户取消订阅公众号事件'''
        pass

    def event_view(self, view_key):
        '''点击菜单跳转链接时的事件推送

        :param view_key: 跳转的链接
        '''

    def event_click(self, click_key):
        '''点击菜单拉取消息时的事件推送

        :param click_key: 自定义菜单接口中KEY值
        '''
        self.reply_debug_text("you clicked  the menu %s" % click_key)

    def event_scan(self, scene_value, ticket):
        '''已关注用户扫码事件

        :param scene_value: ``int`` 型，创建二维码时的二维码scene_id
        :param ticket: 二维码的ticket，可用来换取二维码图片

        .. seealso:: :meth:`event_subscribe`
        '''
        self.reply_debug_text(
            'you scanned the qrcode, scene: '
            '%s, ticket: %s' % (scene_value, ticket))

    def event_template_send_job_finished(self, status):
        '''模板消息发送任务完成事件

        :param status: 消息发送完成之后的状态，包括以下三种：

            #. "success"
            #. "failed:user block"
            #. "failed: system failed"

        '''
        self.log("%s send status: %s" % (self.msg_id, status))

    def on_text(self, text):
        '''接收到文本消息处理方法

        :param text: 接受到的文本
        '''
        if self._debug_to_wechat:
            self.reply_text(text)

    def on_image(self, media_id, pic_url):
        '''接收到图片消息处理方法

        :param media_id: 图片的media_id
        :param pic_url: 图片的下载地址
        '''
        if self._debug_to_wechat:
            self.reply_image(media_id)

    def on_voice(self, media_id, voice_format, recognition):
        '''接受到语音消息处理方法

        :param media_id: 语音的media_id
        :param voice_format: 语音的格式
        :param recognition: 语音的识别的文字，需在公众号中开启，否则为 ``None``
        '''

        if self._debug_to_wechat:
            self.reply_voice(media_id)

    def on_video(self, media_id, thumb_id):
        '''接收到视频消息处理方法

        :param media_id: 视频的media_id
        :param thumb_id: 视频的缩略图media_id
        '''
        if self._debug_to_wechat:
            self.reply_video(media_id)

    def on_shortvideo(self, media_id, thumb_id):
        '''接收到短视频消息处理方法

        :param media_id: 短视频的media_id
        :param thumb_id: 短视频的缩略图media_id
        '''
        if self._debug_to_wechat:
            self.reply_video(media_id)

    def on_location(self, x, y, scale, label):
        '''用户发送地理位置消息的处理方法

        :param x: 纬度
        :param y: 经度
        :param scale: 地图的缩放级别
        :param label: 地理位置的名称

        .. seealso:: :meth:`event_location`
        '''
        self.reply_debug_text(
            "you sent a location: %s(lat:%s, lon:%s, scale:%s)" %
            (x, y, scale, label))

    def on_link(self, url, title, desc):
        '''用户发送链接地址的处理方法

        :param url: 发送的链接地址
        :param title: 链接的标题
        :param desc: 连接的描述
        '''
        self.reply_debug_text("you sent an url: %s, %s" % (title, url))

    def reply_text(self, text):
        '''回复一条文本消息

        :param text: 回复的文本字符串
        '''
        self._reply_type = 'text'
        self._reply = '<Content><![CDATA[%s]]></Content>' % text

    def reply_debug_text(self, text):
        '''debug_to_wechat为True时回复的debug文本消息，否则不回复

        :param text: 回复的debug文本字符串
        '''
        if self._debug_to_wechat:
            self.reply_text("[DEBUG(%s)]: %s" % (self.openid, text))

    def reply_image(self, image_id):
        '''回复一条图片消息

        :param image_id: 图片的media_id
        '''
        self._reply_type = 'image'
        self._reply = (
            '<Image><MediaId><![CDATA[%s]]>'
            '</MediaId></Image>' % image_id)

    def reply_voice(self, voice_id):
        '''回复一条语言消息

        :param voice_id: 回复语音的media_id
        '''
        self._reply_type = 'voice'
        self._reply = (
            '<Voice><MediaId><![CDATA[%s]]>'
            '</MediaId></Voice>' % voice_id)

    def reply_video(self, video_id, title=None, desc=None):
        '''回复一条视频消息

        :param video_id: 回复视频的media_id
        :param title: 回复视频的标题，可不填
        :param desc: 回复视频的描述，可不填
        '''
        self._reply_type = 'video'
        texts = ["<Video>"]
        texts.append("<MediaId><![CDATA[%s]]></MediaId>" % video_id)
        if title:
            texts.append("<Title><![CDATA[%s]]></Title>" % title)
        if desc:
            texts.append("<Description><![CDATA[%s]]></Description>" % desc)
        texts.append("</Video>")
        self._reply = "\n".join(texts)

    def reply_music(self, music_id, title=None,
                    description=None, url=None, hqurl=None):
        '''回复一条歌曲消息

        :param music_id: 歌曲的media_id
        :param title: 歌曲的标题
        :param description: 歌曲的描述
        :param url: 歌曲的url地址
        :param hqurl: 歌曲的高清url地址
        '''
        self._reply_type = 'music'
        texts = ["<Music>"]
        if title:
            texts.append("<Title><![CDATA[%s]]></Title>" % title)
        if description:
            texts.append(
                "<Description><![CDATA[%s]]></Description>" %
                description)
        if url:
            texts.append("<MusicUrl><![CDATA[%s]]></MusicUrl>" % url)
        if hqurl:
            texts.append("<HQMusicUrl><![CDATA[%s]]></HQMusicUrl>" % hqurl)
        texts.append("<ThumbMediaId><![CDATA[%s]]></ThumbMediaId>" % music_id)
        texts.append("</Music>")
        self._reply = '\n'.join(texts)

    def reply_news(self, articles):
        '''回复一条图文消息

        :param articles: 类型为 ``list`` , 包含每一条图文
            每一个图文为一个 ``dict`` ，必须包含 ``title`` , ``description`` ,
            ``picurl`` , ``url`` 四个字段。消息最多包含8条，多余的会自动过滤。
        '''
        items = []
        for atc in articles[:8]:
            items.append(self._get_article_text(**atc))
        body = '<Articles>%s</Articles>' % ''.join(items)
        tpl = ['<ArticleCount>%d</ArticleCount>' % len(articles)]
        tpl.append(body)
        self._reply_type = 'news'
        self._reply = ''.join(tpl)

    def reply_empty(self):
        '''对本条消息不作任何回复'''
        self._reply_type = None

    def _get_article_text(self, title, description, picurl, url):
        texts = ['<item>']
        texts.append('<Title><![CDATA[%s]]></Title>' % title)
        texts.append('<Description><![CDATA[%s]]></Description>' % description)
        texts.append('<PicUrl><![CDATA[%s]]></PicUrl>' % picurl)
        texts.append('<Url><![CDATA[%s]]></Url>' % url)
        texts.append('</item>')
        return '\n'.join(texts)

    def finish(self):
        '''在回复完所有消息之后调用，此处可以使用类型为 :class:`Message` 的
            消息回复对象 :attr:`self.reply_message` , 该对象在回复
            消息为空时为 ``None``

        '''
        pass

    def reply(self):
        ''':returns: 事件或消息处理完成后最终回复给微信的文本内容

        .. note:: 此方法只允许调用一次'''

        if self._processed:
            raise Exception("MessageHandler.reply() 只能调用一次")

        if self._reply_type is None:
            self.log("send empty, user will receive nothing")
            reply_raw = ""
        else:
            reply_message = Message(
                self.message.from_id, self.message.to_id,
                self._reply_type, self._reply, self.message.msg_id,
            )
            self.log("send message: %s" % reply_message)
            self.reply_message = reply_message
            reply_raw = reply_message.build_xml()
        self._finish()
        return reply_raw
