.. _api:

.. module:: yawxt

数据对象模型
----------------

消息对象Message
^^^^^^^^^^^^^^^^

.. autoclass:: Message
    :members:

用户对象User
^^^^^^^^^^^^

.. autoclass:: User
    :members:

地理位置对象Location
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: Location
    :members:

微信HTTP接口WxClient
------------------------------
微信HTTP接口主要封装在 :class:`WxClient` 中

基本属性
    #. appid :attr:`~WxClient.appid`
    #. appsecret :attr:`~WxClient.appsecret`

用户管理
^^^^^^^^^^^^

    #. 获取openid列表 :meth:`~WxClient.get_openid_iter`
    #. 获取用户对象 :meth:`~WxClient.get_user`
    #. 获取关注用户数目 :meth:`~WxClient.get_user_count`
    #. 预览消息 :meth:`~WxClient.preview_message`
    
网页JS开发相关
^^^^^^^^^^^^^^
    #. 从网页授权code获取用户对象 :meth:`~WxClient.get_user_from_web`
    #. 签名网页得到JS配置 :meth:`~WxClient.js_sign`
    
模板消息管理
^^^^^^^^^^^^
    
    #. 设置所属行业 :meth:`~WxClient.set_industry`
    #. 获取所属行业 :meth:`~WxClient.get_industry`
    #. 添加模板库模板 :meth:`~WxClient.add_sys_template`
    #. 删除模板 :meth:`~WxClient.del_template`
    #. 获取模板列表 :meth:`~WxClient.get_template_list`
    #. 发送模板消息 :meth:`~WxClient.send_template_message`

其他
^^^^
    #. 语义理解 :meth:`~WxClient.semantic_parse`

.. autoclass:: WxClient
    :members:
    
消息处理类MessageHandler
----------------------------

基本属性
^^^^^^^^
    #. 用户openid :attr:`~MessageHandler.openid`
    #. 用户 :attr:`~MessageHandler.user`
    #. 消息对象 :attr:`~MessageHandler.message`
    
接收事件消息
^^^^^^^^^^^^
    #. 上报地理位置事件 :meth:`~MessageHandler.event_location`
    #. 关注及扫码关注事件 :meth:`~MessageHandler.event_subscribe`
    #. 取消关注事件 :meth:`~MessageHandler.event_unsubscribe`
    #. 点击菜单链接事件 :meth:`~MessageHandler.event_view`
    #. 点击菜单拉取消息事件 :meth:`~MessageHandler.event_click`
    #. 已关注用户扫码事件 :meth:`~MessageHandler.event_scan`
    #. 模板消息发送任务完成事件 :meth:`~MessageHandler.event_template_send_job_finished`

接收普通消息
^^^^^^^^^^^^

    #. 文本消息 :meth:`~MessageHandler.on_text`
    #. 图片消息 :meth:`~MessageHandler.on_image`
    #. 语音消息 :meth:`~MessageHandler.on_voice`
    #. 视频消息 :meth:`~MessageHandler.on_video`
    #. 短视频消息 :meth:`~MessageHandler.on_shortvideo`
    #. 地址消息 :meth:`~MessageHandler.on_location`
    #. 链接消息 :meth:`~MessageHandler.on_link`
    
回复消息
^^^^^^^^
    
    #. 回复文本 :meth:`~MessageHandler.reply_text`
    #. 回复调试文本 :meth:`~MessageHandler.reply_debug_text`
    #. 回复图像 :meth:`~MessageHandler.reply_image`
    #. 回复语音 :meth:`~MessageHandler.reply_voice`
    #. 回复视频 :meth:`~MessageHandler.reply_video`
    #. 回复图文消息 :meth:`~MessageHandler.reply_news`
    #. 回复空消息 :meth:`~MessageHandler.reply_empty`
    #. 生成回复消息文本 :meth:`~MessageHandler.reply`
    
消息hook
^^^^^^^^
    #. 消息处理前hook :meth:`~MessageHandler.before`
    #. 回复消息生成后hook :meth:`~MessageHandler.finish`
    
注意这些hook每次都会调用，和事件或消息处理函数都会调用，
调用顺序 ``before() -> on_(event_)type() -> after()``
    
.. autoclass:: MessageHandler
    :members:

消息持久化处理类
--------------------

.. currentmodule:: yawxt.persistence

.. autoclass:: PersistMessageHandler
    :members:
    
其他类或方法
------------

.. autofunction:: yawxt.check_signature

.. autofunction:: create_all

.. automodule:: yawxt.exceptions
    :members:
