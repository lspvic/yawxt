yawxt: 又一个微信公众号开发工具箱
=================================

|build-status| |pypi-status| |pypi-pyversions| |docs|

Yet Another WeiXin(wechat) Toolkit

github：https://github.com/lspvic/yawxt/

文档： https://yawxt.readthedocs.io/

实体对象
--------
#. 消息对象 ``yawxt.Message``
#. 用户对象 ``yawxt.User``
#. 位置对象 ``yawxt.Location``

使用数据对象可以很好的管理和访问微信数据资源，如::
    
    user.nickname, user.headimgurl, user.city
    location.latitude, location.longitude, location.time
    message.msg_type, message.msg_id, message.create_time

公众号API
---------
类 ``yawxt.WxClient`` 封装公众号API

.. code-block:: python

    >>> from yawxt import WxClient
    >>> client = WxClient("appid", "appsecret")
    >>> it = client.get_openid_iter()
    >>> openid = next(it)
    >>> openid
    'o9KLls70ReakhjebmHUYxjbz9K8c'
    >>> user = client.get_user(openid)
    >>> user
    {"openid": "o9KLls70ReakhjebmHUYxjbz9K8c", "nickname": "yawxt", ...}
    >>> user.city
    '杭州'
    
    
消息对话
--------
类 ``yawxt.MessageHandler`` 处理接收消息事件

.. code-block:: python

    from yawxt import MessageHandler, WxClient, check_signature
    
    # 定义消息回复内容
    class Handler(MessageHandler):
    
        # 当收到一条文本消息时
        def on_text(self, text):
            # 回复一条文本消息
            # 可以使用已定义的user对象
            self.reply_text("你好:%s" % self.user.nickname)
        
        # 当收到地理位置上报事件时
        def event_location(self,location):
            # 保存地理位置
            redis.hset("location::%s" % self.openid, 
                {"lat": location.latitude, "lon": location.longitude})
                
        # 当收到一条图片消息时
        def on_image(self, media_id, pic_url):        
            # 可以调用公众号API，下载到本地
            r = self.client.download_image(media_id)
            with open("/path/to/images/%s.jpg" % media_id, "rb") as f:
                f.write(r.content)
            # 回复同样的图片
            self.reply_image(media_id)            

    client = WxClient(appid, secret, token)
    
    # 在web框架中回复消息，以Flask为例
    app = Flask(__name__)
    session_maker = sessionmaker(bind=engine)
    token = "token"  # 公众号后台配置Token
    @app.route('/wechat', methods=["GET", "POST"])
    def wechat():
        signature = request.args.get('signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        if not check_signature(token, timestamp, nonce, signature):
            return "Messages not From Wechat"
        if request.method == "GET":
            return request.args.get('echostr')
            
        msg = PersistMessageHandler(request.data, wechat_account,
                                db_session_maker=session_maker,
                                debug_to_wechat=app.debug)
        return msg.reply()
        
消息持久化
------------

使用类 ``yawxt.persistence.PersistMessageHandler`` ，不做任何处理就能够直接将接收的消息、
用户信息、上报位置信息保存到数据库中：

.. code-block:: python

    from yawxt.persistence import PersistMessageHandler
    
    Session = session_maker(bind=engine)
    message = PersistMessageHandler(content, client=client, 
        db_session_maker=Session, debug_to_wechat=True)
    return_str = message.reply()
    
继承 ``PersistMessageHandler`` ，只关注自己的处理逻辑，所有消息的接收
与发送都持久化到数据库中了。
    
更多的例子在 `examples <https://github.com/lspvic/yawxt/tree/master/examples>`_ 文件夹下面

安装
----
使用pip安装yawxt:

``pip install yawxt``

如果要使用消息持久化，还需要安装sqlalchemy及数据库驱动，如mysql的PyMySQL：

``pip install sqlalchemy PyMySQL``

.. |build-status| image:: https://img.shields.io/travis/lspvic/yawxt.svg
    :target: https://travis-ci.org/lspvic/yawxt
    
.. |pypi-status| image:: https://img.shields.io/pypi/v/yawxt.svg
    :target: https://pypi.python.org/pypi/yawxt
    
.. |pypi-pyversions| image:: https://img.shields.io/pypi/pyversions/yawxt.svg
    :target: https://pypi.python.org/pypi/yawxt
    
.. |docs| image:: https://readthedocs.org/projects/yawxt/badge/?version=latest
   :alt: Documentation Status
   :target: https://readthedocs.org/projects/yawxt/
     