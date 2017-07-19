#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import json

import requests

from zhihu_common import *


class ZhihuClient:

    """知乎客户端类，内部维护了自己专用的网络会话，可用cookies或账号密码登录."""

    def __init__(self, cookies=None):
        """创建客户端类实例.

        :param str cookies: 见 :meth:`.login_with_cookies` 中 ``cookies`` 参数
        :return: 知乎客户端对象
        :rtype: ZhihuClient
        """
        self._session = requests.Session()
        self._session.headers.update(Default_Header)
        self.proxies = None
        if cookies is not None:
            assert isinstance(cookies, str)
            self.login_with_cookies(cookies)

    def login_with_cookies(self, cookies):
        """使用cookies文件或字符串登录知乎

        :param str cookies:
            ============== ===========================
            参数形式       作用
            ============== ===========================
            文件名         将文件内容作为cookies字符串
            cookies 字符串  直接提供cookies字符串
            ============== ===========================
        :return: 无
        :rtype: None
        """
        if os.path.isfile(cookies):
            with open(cookies) as f:
                cookies = f.read()
        cookies_dict = json.loads(cookies)
        self._session.cookies.update(cookies_dict)

    def __getattr__(self, item: str):
        """本函数用于获取各种类，如 `Answer` `Question` 等.

        :支持的形式有:
            1. client.answer()
            2. client.author()
            3. client.collection()
            4. client.column()
            5. client.post()
            6. client.question()
            7. client.topic()

            参数均为对应页面的url，返回对应的类的实例。
        """
        def getter(url):
            return getattr(module, item.capitalize())(url,
                                                      session=self._session)
        attr_list = ['zhihu_post', 'zhihu_question', 'zhihu_topic','zhihu_search']
        if item.lower() in attr_list:
            module = importlib.import_module(item.lower())
            return getter
