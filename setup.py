# -*- coding: utf-8 -*-

import os
import io
import re
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='yawxt',
    version=find_version("yawxt", "__init__.py"),
    packages=['yawxt', ],
    author='lspvic',
    author_email='lspvic@qq.com',
    install_requires=[
        'requests_oauthlib',
        'pyOpenSSL;python_version=="2.6"'
    ],
    url='http://github.com/lspvic/yawxt',
    license='MIT License',
    description='又一个微信公众号开发工具箱 Yet Another WeiXin(wechat) Tookit',
    long_description=read("README.rst"),
    keywords=['wechat', 'weixin', 'Official Account', '微信', '公众号'],
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: Chinese (Simplified)',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    )
