# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = 'yawxt',
    version = '0.1.dev1',
    packages = ['yawxt',],
    author = 'lspvic',
    author_email = 'lspvic@qq.com',
    install_requires = [ 'requests_oauthlib', 'requests', 'oauthlib'],
    url = 'http://github.com/lspvic/yawxt',
    license = 'MIT License',
    description = '又一个微信开发工具箱 Yet Another WeiXin Tookit',
    keywords=['wechat', 'weixin', '微信'],
    classifiers  = [
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    ) 
