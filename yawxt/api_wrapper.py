# -*- coding:utf-8 -*-

import time
import hashlib
import random
import string
from functools import wraps
import logging
import requests
import json

from requests_oauthlib import OAuth2Session as O2Session
from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2 import TokenExpiredError, OAuth2Error
from oauthlib.oauth2.rfc6749.parameters import prepare_token_request
from oauthlib.oauth2.rfc6749.clients.base import URI_QUERY

from .models import User

logger = logging.getLogger(__name__)
__all__ = ["APIError", "OfficialAccount"]

class APIError(Exception):
    '''微信API调用异常类，通过 :class:`~yawxt.OfficalAccount` 调用微信API错误码
        不是0时抛出此异常
    
    :param errcode: 错误码，和微信全局错误码一致
    :param errmsg: 错误消息，微信API调用错误消息
    '''
    def __init__(self, errcode, errmsg):
        self.errcode = errcode
        self.errmsg = errmsg
        
    def __str__(self):
        return "API Exception, code: %s, msg: %s" %(self.errcode, self.errmsg)


class WechatApplicationClient(BackendApplicationClient):
    def __init__(self, client_id, **kwargs):
        super(
            WechatApplicationClient,
            self).__init__(
            client_id,
            default_token_placement=URI_QUERY,
            **kwargs)

    def prepare_request_body(self, **kwargs):
        return prepare_token_request('client_credential', **kwargs)

class RestClient(O2Session):

    def __init__(self, token_url = None, token_kwargs = None):
        self.token_url = token_url
        self.token_kwargs = token_kwargs or {}
        super(RestClient, self).__init__(
            client=WechatApplicationClient("wechat_client"))

    def request(self, method, url, data=None, headers=None, withhold_token=False,
                client_id=None, client_secret=None, **kwargs):
        if url not in OfficialAccount.URLS:
            return super(RestClient, self).request(method, url, data=data, headers=headers, 
                withhold_token=withhold_token, client_id=client_id, client_secret=client_secret, **kwargs)

        api_type = url
        url = OfficialAccount.URLS[url]
        try:
            r = super(RestClient, self).request(method, url, data=data, headers=headers, 
                withhold_token=withhold_token, client_id=client_id, client_secret=client_secret, **kwargs)
            result = r.json()
            if 'errcode' in result and result["errcode"] in (40001, 40014, 41001, 42001):
                raise OAuth2Error(
                        status_code=result['errcode'],
                        description=result["errmsg"])
        except OAuth2Error as e:
            logger.debug(
                    "%s request token error, errcode: %s, message: %s"
                    % (api_type, e.status_code, e.description)
                )
            token = self.fetch_token(
                self.token_url,
                method='GET',
                **self.token_kwargs)
            logger.debug("fetch oauth2 access_token: %s" % token)
            r = super(RestClient, self).request(method, url, data=data, headers=headers, 
                withhold_token=withhold_token, client_id=client_id, client_secret=client_secret, **kwargs)
            result = r.json()
        if 'errcode' in result and result["errcode"] != 0:
            raise APIError(result["errcode"], result["errmsg"])
        return result

class OfficialAccount():
    '''公众号API类，封装大部分公众号RESTful API的接口
    
    :param appid: 微信公众号appID
    :param secret: 微信公众号appsecret
    
    .. todo:: 完成用户管理的标签管理，共8个API
    .. todo:: 完成用户的备注功能， 共2个API
    .. todo:: 完成用户的拉黑功能，共2个API
    
    '''

    URLS = {
        # access_token
        'token': 'https://api.weixin.qq.com/cgi-bin/token',
        # 用户信息
        'user_list': 'https://api.weixin.qq.com/cgi-bin/user/get',
        'user_info': 'https://api.weixin.qq.com/cgi-bin/user/info',
        'msg_preview': 'https://api.weixin.qq.com/cgi-bin/message/mass/preview',
        'voice_download': 'https://file.api.weixin.qq.com/cgi-bin/media/get',
        'semantic': 'https://api.weixin.qq.com/semantic/semproxy/search',
        
        # 自定义菜单
        # 创建 POST
        'menu_create': 'https://api.weixin.qq.com/cgi-bin/menu/create',
        # 查询 GET
        'menu_get':'https://api.weixin.qq.com/cgi-bin/menu/get',
        # 删除 GET
        'menu_delete': 'https://api.weixin.qq.com/cgi-bin/menu/delete',
        # 
        'web_token': 'https://api.weixin.qq.com/sns/oauth2/access_token',
        'web_user_info': 'https://api.weixin.qq.com/sns/userinfo',
        'web_refresh_token': 'https://api.weixin.qq.com/sns/oauth2/refresh_token',

        'jsapi': 'https://api.weixin.qq.com/cgi-bin/ticket/getticket',

        'template_messge_send': 'https://api.weixin.qq.com/cgi-bin/message/template/send',
        'add_tmplate': 'https://api.weixin.qq.com/cgi-bin/template/api_add_template',
        'set_industry': 'https://api.weixin.qq.com/cgi-bin/template/api_set_industry',
        'get_industry': 'https://api.weixin.qq.com/cgi-bin/template/get_industry',
        'get_templates': 'https://api.weixin.qq.com/cgi-bin/template/get_all_private_template',
        'del_template': 'https://api.weixin.qq.com/cgi-bin/template/del_private_template',
    }

    def __init__(self, appid, secret):
        self.appid = appid
        self.secret = secret
        self.client = RestClient(token_url=self.URLS["token"],
            token_kwargs={"appid": self.appid, "secret": self.secret})

        self._js_ticket = None


    def _request_user_list(self, next_openid):
        p = {'next_openid': next_openid}
        return self.client.get('user_list', params=p)
        
    def get_users_iterator(self):
        '''
        :rtype: generator
        
        :returns: 关注公众号所有用户的迭代器，可以使用 :meth:`next` 函数
            或 ``for`` 循环得到每一个用户的openid：

            .. code-block:: python
            
                it = account.get_users_iterator()
                first_openid = next(it)
                for openid in it:
                    do_something(openid)

        可以使用 ``list(account.get_users_iterator())`` 直接获取所有用户的openid列表，
        要获取关注公众号的总用户数，请使用 :meth:`get_users_count` , 尤其是用户数
        量比较多的情况下
        '''
        next_openid = ''
        flag = True
        while next_openid or flag:
            flag = False
            result = self._request_user_list(next_openid)
            for openid in result["data"]["openid"]:
                yield openid
            next_openid = result["data"].get("next_openid", "")

    def get_users_count(self):
        '''获取关注公众号的总用户人数
        
        :rtype: int
        '''
        result = self._request_user_list('')
        return result["total"]
    
    def get_user_info(self, openid):
        '''获取用户对象
        
        :param openid: 要获取信息用户的openid
        :returns: 用户对象 
        :rtype:   User
        
        '''
        p = {'openid': openid}
        return User.from_dict(self.client.get('user_info', params=p))

    def preview_message(self, openid, text):
        '''消息预览接口，给指定用户发送消息，此接口只是为了方便开发者查看消息的样式和排版
        
        :param openid: 用户的openid
        :param text: 发送消息的文本内容
        :returns: 返回消息id，发送文本时消息id为 ``None``
        
        .. note:: 此消息每日调用限制100次，请勿滥用
        .. todo:: 此接口可以发送文本、语音、图片、视频、卡券，待实现
        '''
        data = {"touser": openid, "text": {"content": text}, "msgtype": "text"}
        r = self.client.post('msg_preview', data=json.dumps(data, ensure_ascii=False).encode("utf-8"))
        return r["msg_id"] if 'msg_id' in r else None

    def get_web_user_info(self, code):
        web_client = OAuth2Session(
            client=BackendApplicationClient(
                "wechat_web_client",
                default_token_placement='query'),
            auto_refresh_url=self.URLS['web_refresh_token'],
            auto_refresh_kwargs={
                'appid': self.appid})
        web_token = web_client.fetch_token(
            self.URLS['web_token'],
            code=code,
            appid=self.appid,
            secret=self.secret)
        openid = web_token['openid']
        yield openid
        r = web_client.get(
            self.URLS["web_user_info"], params={
                'openid': openid})
        r.encoding = 'utf-8'
        yield r.json()

    @property
    def js_ticket(self):
        '''获得JS API调用的临时票据jsapi_ticket
        
        :returns: 票据 ``dict`` , 包含 ``ticket`` , ``expires_at`` , ``expires_at`` 等字段
        '''
        logger.debug("current js ticket: %s" % self._js_ticket)
        if not self._js_ticket or self._js_ticket["expires_at"] < time.time():
            self._js_ticket = self.client.get('jsapi', params={"type": "jsapi"})
            self._js_ticket["expires_at"] = time.time(
            ) + int(self._js_ticket["expires_in"])
            logger.debug("get new js ticket: %s" % self._js_ticket)
        return self._js_ticket

    def get_js_sign(self, url, debug=True):
        '''JS-SDK步骤三：config接入接口配置生成，这个过程需要在服务器端完成
        
        :param url: js注入的url
        :param debug: js调试模式，默认为开启
        :returns: JS-SDK config接入接口配置信息
        :rtype: dict        
        '''
        result = {
            'debug': "true" if debug else "false",
            'nonceStr': ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15)),
            'jsapi_ticket': self.js_ticket["ticket"],
            'timestamp': int(time.time()),
            'url': url
        }
        tmpStr = '&'.join(['%s=%s' % (key.lower(), result[key])
                           for key in sorted(result)])
        result['signature'] = hashlib.sha1(tmpStr.encode()).hexdigest()
        result['appId'] = self.appid
        del result['jsapi_ticket']
        return result

    def set_industry(self, industry_id1, industry_id2):
        '''设置模板消息的公众号的所属行业，需要设置两个
        
        :param industry_id1: 设置第一行业id，在1-41之间
        :param industry_id2: 设置第二行业id，在1-41之间
        '''
        self.client.post("set_industry", json={
            "industry_id1": str(industry_id1),
            "industry_id2": str(industry_id2)
        })
        
    def get_industry(self):
        '''获取模板消息的公众号的所属行业
        
        :rtype: dict
        :returns: 两个所属行业代码的字典，例如
        
            .. code-block:: json
            
                {"primary_industry":
                    {"first_class":"运输与仓储",
                    "second_class":"快递"},
                "secondary_industry":
                    {"first_class":"IT科技",
                    "second_class":"互联网|电子商务"}
                }
            
        '''
        
        return self.client.get("get_industry")

    def add_template(self, short_id):
        '''从系统模板库选择模板设置为公众号模板
        
        :param short_id: 系统模板库模板id
        :returns: 设置为公众号模板后的模板id
        :rtype: str
        '''        
        return self.client.post("add_tmplate", json={
            "template_id_short": short_id})["template_id"]
            
    def delete_template(self, template_id):
        '''删除公众号模板
        
        :param template_id: 要删除的模板id
        '''
        self.client.post("del_template", json={
            "template_id": template_id})
            
    def get_template_list(self):
        '''获取公众号的所有消息模板列表
        
        :returns: 消息模板列表
        :rtype: list
        '''
        return self.client.get("get_templates")["template_list"]

    def send_template_message(self, to_openid, template_id, data, 
        miniprogram_id=None, miniprogram_path=None, url=None):
        '''给用户发送模板消息
        
        :param to_openid: 要发送的用户的openid
        :param template_id: 发送的消息模板id
        :param data: 模板的具体数据
        :param miniprogram_id: 要跳转的小程序id, 可不填
        :param miniprogram_path: 要跳转的小程序路径
        :param url: 要跳转的url，同时设置小程序，小程序优先
        :returns: 发送消息的id
        '''
        content = {
            "touser": to_openid,
            "template_id": template_id,
            "data": data,
        }
        if miniprogram_id is not None:
            content.update({
                "miniprogram": {
                    "appid": miniprogram_id,
                    "pagepath": miniprogram_path,
                }
            })
        elif url is not None:
            content["url"] = url
        return self.client.post("template_messge_send", json=content)["msgid"]        

    def get_voice(self, media_id):
        p = {'media_id': media_id}
        return self.client.get('voice_download', params=p)
        
    def get_semantic(self, query, city=None,
                     category=[
            'restaurant', 'map', 'nearby', 'coupon', 'travel',
            'hotel', 'train', 'flight', 'weather', 'stock', 'remind',
            'telephone', 'movie', 'music', 'video', 'novel',
            'cookbook', 'baike', 'news', 'tv', 'app', 'nstruction',
            'tv_instruction', 'car_instruction', 'website', 'search'],
        lat=None, lon=None, region=None, uid=None, 
    ):
        '''语义理解接口. 具体请参见微信语义接口开发文档

        :param query: 需要解析的文本字符串
        :param city: 所在的城市
        :param uid: 微信用户openid，可以使用使用上下文理解功能
        :param category: 理解场景的服务类型，默认包含所有类别
        :param lat: 地理位置纬度
        :param lon: 地理位置经度
        :param region: 所在的区域
        :rtype: dict
        :returns: 参见微信语义接口开发文档
        
        .. note:: 此接口问题比较多，异常返回而且错误码未知，请谨慎使用
        '''
        data = {
            'query': query,
            'category': ','.join(category),
            'appid': self.appid
        }
        if uid is not None:
            data['uid'] = uid
        if lat is not None and lon is not None:
            data['latitude'] = lat
            data['longitude'] = lon
        if city is not None:
            data['city'] = city
        if region is not None:
            data['region'] = region

        return self.client.post('semantic', json=data)
