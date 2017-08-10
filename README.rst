yawxt: Yet Another WeiXin Toolkit
=======================
又一个微信开发工具箱

公众号API
-----------

.. code-block:: python

    >>> from yawxt import OfficialAccount
    >>> account = OfficialAccount("appid", "appsecret")
    >>> openid = next(account.get_users_iterator())
    >>> openid
    'o9KLls70ReakhjebmHUYxjbz9K8c'
    >>> user = account.get_user_info(openid)
    >>> user
    User(openid=o9KLls70ReakhjebmHUYxjbz9K8c, nickname=yawxt)
    >>> user.city
    '杭州'
    
    
消息对话
----------

.. code-block:: python

    # 定义消息回复内容
    from yawxt import MessageProcessor, OfficialAccount
    class Processor(MessageProcessor):
        def on_text(self, text):
            # 回复一条文本消息
            self.reply_text("%s, 你好" % self.user.nickname)
        def event_location(self,loc):
            # 保存地理位置
            redis.hset("location::%s" % self.openid, 
                {"lat": loc.latitude, "lon": loc.longitude})
        def on_video(self, media_id):
            
            
    # 在web框架中回复消息，以Flask为例
    from yawxt import OfficialAccount, check_signature
    account = OfficialAccount(appid, secret, token)
    
    @app.route('/wechat', methods = ["GET", "POST"])
    def req():
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        if not check_signature(token, timestamp, nonce, signature):
            return "Messages not From Wechat"
        if request.method == "GET":
            return request.args.get('echostr')
        msg = Message(request.data, account, debug_to_wechat=app.debug)
        return msg.reply()
        
消息持久化
------------

继承 ``yawxt.persistence.PersistentMessageProcessor`` ，可以直接将接收的消息、
用户信息、上报位置信息保存到数据库中：

.. code-block:: python

    from yawxt.persistence import PersistentMessageProcessor
        
    message = PersistentMessageProcessor(content, account=account, 
        db_session_maker=session_maker(), debug_to_wechat=True)
    return_str = message.reply()
    
更多的例子在example文件夹下面

安装
-----
使用pip安装yawxt:

``pip install yawxt``

如果要使用消息持久化，还需要安装sqlalchemy及数据库驱动，如mysql的PyMySQL：

``pip install sqlalchemy PyMySQL``

文档
-----
https://yawxt.readthedocs.com/
    
    