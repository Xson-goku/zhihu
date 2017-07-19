#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import random
from datetime import datetime

from zhihu_common import *
from zhihu_base import BaseZhihu
from bs4 import BeautifulSoup

import logging
import logging.config

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("zhihu_topic.py")

class Zhihu_topic(BaseZhihu):

    """答案类，请使用``ZhihuClient.topic``方法构造对象."""

    @class_common_init(re_topic_url)
    def __init__(self, url, name=None, session=None):
        """创建话题类实例.

        :param url: 话题url
        :param name: 话题名称，可选
        :return: Topic
        """
        self.url = url
        self._session = session
        self._name = name
        self._id = int(re_topic_url.match(self.url).group(1))

    @property
    def id(self):
        """获取话题Id（网址最后那串数字）

        :return: 话题Id
        :rtype: int
        """
        return self._id

    @property
    @check_soup('_name')
    def name(self):
        """获取话题名称.

        :return: 话题名称
        :rtype: str
        """
        return self.soup.find('h1').text

    @property
    def questions(self):
        """获取话题下的所有问题（按时间降序排列）

        :return: 话题下所有问题，返回生成器
        :rtype: Question.Iterable
        """               
        from zhihu_question import Zhihu_question
        question_url = Topic_Questions_Url.format(self.id)
        params = {'page': 1}
        older_time_stamp = int(time.time()) * 1000          
        cnt = 1
        while True:
            res = None
            try:
                res = self._session.get(question_url, params=params)
            except Exception as e:
                print("exception ocurred at questions in zhihu_topic, retry time is " + str(cnt))
                logger.error("exception ocurred at questions in zhihu_topic, retry time is" + str(cnt))
                cnt = cnt + 1
                if cnt == 4:
                    print("skip a brand, url is:" + question_url)
                    return
                time.sleep(30)
                continue
            content = res.content.decode('utf-8')
            soup = BeautifulSoup(res.content, 'lxml')
            if soup.find('div', class_='error') is not None:
                return
            questions = soup.find_all('div', class_='question-item')
            if not questions:#https://www.zhihu.com/topic/20041651/
                return
            try:
                questions = list(filter(lambda x: int(x.h2.span['data-timestamp']) < older_time_stamp, questions))
            except Exception as e:
                logger.error('exception ocurred at questions of zhihu_topic, topic url is:' + self.url)
                logger.error(str(e))
                return
            for qu_div in questions:
                url = Zhihu_URL + qu_div.h2.a['href']
                title = qu_div.h2.a.text.strip()
                creation_time = datetime.fromtimestamp(
                        int(qu_div.h2.span['data-timestamp']) // 1000)
                yield Zhihu_question(url, title, creation_time=creation_time,
                               session=self._session)            
            older_time_stamp = int(questions[-1].h2.span['data-timestamp'])
            time.sleep(random.randint(15,30))            
            params['page'] += 1
