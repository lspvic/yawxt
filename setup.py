# -*- coding: utf-8 -*-

import codecs
from setuptools import setup

with codecs.open("README.rst", "r", "utf8") as f:
    readme = f.read()

setup(
    name = 'yawxt',
    version = '0.1.dev1',
    packages = ['yawxt',],
    author = 'lspvic',
    author_email = 'lspvic@qq.com',
    install_requires = [
        'requests_oauthlib',
        'pyOpenSSL;python_version=="2.6"'
    ],
    url = 'http://github.com/lspvic/yawxt',
    license = 'MIT License',
    description = '又一个微信开发工具箱 Yet Another WeiXin Tookit',
    long_description = readme,
    keywords=['wechat', 'weixin', '微信'],
    classifiers  = [
        'Intended Audience :: Developers',
        'Natural Language :: Chinese',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    ) 
