#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from datetime import datetime
import re

from zhihu_common import *
from zhihu_base import BaseZhihu

import logging
import logging.config

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("zhihu_question.py")


class Zhihu_question(BaseZhihu):
    """问题类，请使用``ZhihuClient.question``方法构造对象."""

    @class_common_init(re_question_url, trailing_slash=False)
    def __init__(self, url, title=None, followers_num=None,
                 answer_num=None, creation_time=None, author=None,
                 session=None):
        """创建问题类实例.

        :param str url: 问题url. 现在支持两种 url

            1. https://www.zhihu.com/question/qid
            2. https://www.zhihu.com/question/qid?sort=created

            区别在于,使用第一种,调用 ``question.answers`` 的时候会按投票排序返回答案;
            使用第二种, 会按时间排序返回答案, 后提交的答案先返回
        
        :param str title: 问题标题，可选,
        :param int followers_num: 问题关注人数，可选
        :param int answer_num: 问题答案数，可选
        :param datetime.datetime creation_time: 问题创建时间，可选
        :param Author author: 提问者，可选
        :return: 问题对象
        :rtype: Question
        """
        self._session = session
        self._url = url
        self._title = title
        self._answer_num = answer_num
        self._followers_num = followers_num
        self._id = int(re.match(r'.*/(\d+)', self.url).group(1))
        self._author = author
        self._creation_time = creation_time
        self._logs = None
        self._deleted = None

    @property
    def url(self):
        # always return url like https://www.zhihu.com/question/1234/
        url = re.match(re_question_url_std, self._url).group()
        return url if url.endswith('/') else url + '/'

    @property
    def id(self):
        """获取问题id（网址最后的部分）.

        :return: 问题id
        :rtype: int
        """
        return self._id

    @property
    @check_soup('_qid')
    def qid(self):
        """获取问题内部id（用不到就忽视吧）

        :return: 问题内部id
        :rtype: int
        """
        return int(self.soup.find(
            'div', id='zh-question-detail')['data-resourceid'])

    @property
    @check_soup('_xsrf')
    def xsrf(self):
        """获取知乎的反xsrf参数（用不到就忽视吧~）

        :return: xsrf参数
        :rtype: str
        """
        x = self.soup.find('input', attrs={'name': '_xsrf'})
        if x:
            return x['value']
        return ''
        #return self.soup.find('input', attrs={'name': '_xsrf'})['value']

    @property
    @check_soup('_html')
    def html(self):
        """获取页面源码.

        :return: 页面源码
        :rtype: str
        """
        return self.soup.prettify()

    @property
    @check_soup('_title')
    def title(self):
        """获取问题标题.

        :return: 问题标题
        :rtype: str
        """        
        count = 2
        while(count):
            try:
                return self.soup.find('h2', class_='zm-item-title') \
                    .text.replace('\n', '')
            except Exception as e:
                count = count - 1
                if not count:
                    logger.info('exception ocurred in zhihu_question at title, question url is:' + self._url)
                    logger.error(str(e))
                    return ''
                logger.info('sleep in zhihu_question at title, question url is:' + self.url)
                ##time.sleep(1)
                self.soup = BeautifulSoup(self._session.get(self._url).content)
                continue

    @property
    @check_soup('_details')
    def details(self):
        """获取问题详细描述，目前实现方法只是直接获取文本，效果不满意……等更新.

        :return: 问题详细描述
        :rtype: str
        """
        count = 2
        while(count):
            try:
                return self.soup.find("div", id="zh-question-detail").div.text.replace('\n', '')
            except Exception as e:
                count = count - 1
                if not count:
                    logger.info('exception ocurred in zhihu_question at details, question url is:' + self._url)
                    logger.error(str(e))
                    return ''
                logger.info('sleep in zhihu_question at details, question url is:' + self.url)
                ##time.sleep(1)
                self.soup = BeautifulSoup(self._session.get(self._url).content)
                continue
        #return self.soup.find("div", id="zh-question-detail").div.text.replace('\n', '')

    @property
    @check_soup('_answer_num')
    def answer_num(self):
        """获取问题答案数量.

        :return: 问题答案数量
        :rtype: int
        """
        answer_num_block = self.soup.find('h3', id='zh-question-answer-num')
        # 当0人回答或1回答时，都会找不到 answer_num_block，
        # 通过找答案的赞同数block来判断到底有没有答案。
        # （感谢知乎用户 段晓晨 提出此问题）
        if answer_num_block is None:
            if self.soup.find('span', class_='count') is not None:
                return 1
            else:
                return 0
        return int(answer_num_block['data-num'])

    @property
    @check_soup('_follower_num')
    def follower_num(self):
        """获取问题关注人数.

        :return: 问题关注人数
        :rtype: int
        """
        count = 2
        while(count):
            try:
                follower_num_block = self.soup.find('div', class_='zg-gray-normal')
                # 无人关注时 找不到对应block，直接返回0
                if follower_num_block is None or follower_num_block.strong is None:
                    return 0
                return int(follower_num_block.strong.text)
            except Exception as e:
                count = count - 1
                if not count:
                    logger.info('exception ocurred in zhihu_question at follower_num, question url is:' + self._url)
                    logger.error(str(e))
                    return 0
                logger.info('sleep in zhihu_question at follower_num, question url is:' + self._url)
                ###time.sleep(5)
                self.soup = BeautifulSoup(self._session.get(self._url).content)
                continue
        
        
    @property
    @check_soup('_visit_num')
    def visit_num(self):
        """获取问题浏览人数.
        """
        count = 2
        while(count):
            try:
                visit_num_block = self.soup.find_all('div', class_='zg-gray-normal')[-1]
                # 无人关注时 找不到对应block，直接返回0
                if visit_num_block is None or visit_num_block.strong is None:
                    return 0
                return int(visit_num_block.strong.text) 
            except Exception as e:
                count = count - 1
                if not count:
                    logger.info('exception ocurred in zhihu_question at visit_num, question url is:' + self._url)
                    logger.error(str(e))
                    return 0
                logger.info('sleep in zhihu_question at visit_num, question url is:' + self._url)
                content = self._session.get(self._url).content
                print("----------------")
                print(content)
                print("!!!!!!!!!!!!!!!")
                time.sleep(10)
                self.soup = BeautifulSoup(content)
                continue
        

    @property
    @check_soup('_topics')
    def topics(self):
        """获取问题所属话题.

        :return: 问题所属话题
        :rtype: Topic.Iterable
        """
        from zhihu_topic import Zhihu_topic

        for topic in self.soup.find_all('a', class_='zm-item-tag'):
            yield Zhihu_topic(Zhihu_URL + topic['href'], topic.text.replace('\n', ''),
                        session=self._session)

    @property
    def followers(self):
        """获取关注此问题的用户

        :return: 关注此问题的用户
        :rtype: Author.Iterable
        :问题: 要注意若执行过程中另外有人关注，可能造成重复获取到某些用户
        """
        self._make_soup()
        followers_url = self.url + 'followers'
        for x in common_follower(followers_url, self.xsrf, self._session):
            yield x

    @property
    def answers(self):
        """获取问题的所有答案.

        :return: 问题的所有答案，返回生成器
        :rtype: Answer.Iterable
        """
        from zhihu_author import Zhihu_author
        from zhihu_answer import Zhihu_answer

        self._make_soup()

        # TODO: 统一逻辑. 完全可以都用 _parse_answer_html 的逻辑替换
        if self._url.endswith('sort=created'):
            pager = self.soup.find('div', class_='zm-invite-pager')
            if pager is None:
                max_page = 1
            else:
                max_page = int(pager.find_all('span')[-2].a.text)

            for page in range(1, max_page + 1):
                if page == 1:
                    soup = self.soup
                else:
                    url = self._url + '&page=%d' % page
                    soup = BeautifulSoup(self._session.get(url).content)
                error_answers = soup.find_all('div', id='answer-status')
                for each in error_answers:
                    each['class'] = 'zm-editable-content'
                answers_wrap = soup.find('div', id='zh-question-answer-wrap')
                # 正式处理
                authors = answers_wrap.find_all(
                    'div', class_='zm-item-answer-author-info')
                urls = answers_wrap.find_all('a', class_='answer-date-link')
                up_num = answers_wrap.find_all('div',
                                               class_='zm-item-vote-info')
                contents = answers_wrap.find_all(
                    'div', class_='zm-editable-content')
                assert len(authors) == len(urls) == len(up_num) == len(
                    contents)
                for author, url, up_num, content in \
                        zip(authors, urls, up_num, contents):
                    a_url, name, motto, photo = parser_author_from_tag(author)
                    author_obj = Zhihu_author(a_url, name, motto, photo_url=photo,
                                        session=self._session)
                    url = Zhihu_URL + url['href']
                    up_num = int(up_num['data-votecount'])
                    content = answer_content_process(content)
                    yield Zhihu_answer(url, self, author_obj, up_num, content,
                                 session=self._session)
        else:
            pagesize = 10
            new_header = dict(Default_Header)
            new_header['Referer'] = self.url
            params = {"url_token": self.id,
                      'pagesize': pagesize,
                      'offset': 0}
            data = {'_xsrf': self.xsrf,
                    'method': 'next',
                    'params': ''}
            for i in range(0, (self.answer_num - 1) // pagesize + 1):
                time.sleep(0.01)
                if i == 0:
                    # 修正各种建议修改的回答……
                    error_answers = self.soup.find_all('div',
                                                       id='answer-status')
                    for each in error_answers:
                        each['class'] = 'zm-editable-content'
                    answers_wrap = self.soup.find('div',
                                                  id='zh-question-answer-wrap')
                    if not answers_wrap:
                        logger.error("answers_wrap is none")
                        continue
                    # 正式处理
                    #authors = answers_wrap.find_all(
                    #    'div', class_='zm-item-answer-author-info')
                    urls = answers_wrap.find_all('a', class_='answer-date-link')
                    up_num = answers_wrap.find_all('div',
                                                   class_='zm-item-vote-info')
                    com_num = answers_wrap.find_all('a', class_='toggle-comment')
                    cre_time = answers_wrap.find_all('a', class_='answer-date-link')
                    author_info = answers_wrap.find_all('div', class_='zm-item-answer-author-info')
                    contents = answers_wrap.find_all(
                        'div', class_='zm-editable-content')
                    #assert len(authors) == len(urls) == len(up_num) == len(
                    #    contents)
                    for url, up_num, com_num, cre_time, author_info, content in \
                            zip(urls, up_num, com_num, cre_time, author_info, contents):
                        #a_url, name, motto, photo = parser_author_from_tag(
                        #    author)
                        #author_obj = Zhihu_author(a_url, name, motto, photo_url=photo,
                        #                    session=self._session)
                        url = Zhihu_URL + url['href']
                        up_num = int(up_num['data-votecount'])
                        #content = answer_content_process(content)
                        
                        s = com_num.text
                        m = re.findall(r'(\w*[0-9]+)\w*',s)
                        if m:
                            com_num = int(m[0])
                        else:
                            com_num = 0
                            
                        s = cre_time.text
                        results = re.search(r'\d{4}-\d{2}-\d{2}', s)
                        if results:
                            cre_time = results.group(0)
                            timeArray = time.strptime(cre_time, "%Y-%m-%d")
                            cre_time = int(time.mktime(timeArray))
                        else:
                            cre_time = 0
                        
                        badge = 0
                        if author_info.find('span', class_='icon icon-badge-identity icon-badge'):
                            badge = 1
                        elif author_info.find('span', class_='icon icon-badge-best_answerer'):
                            badge = 2
                        elif author_info.find('span', class_='icon icon-badge-id-an icon-badge'):
                            badge = 3   
                        ans_detail = content.text.replace('\n', '')
                        yield Zhihu_answer(url, self, author_badge=badge, upvote_num=up_num, 
                                     comment_num=com_num, creation_time=cre_time, detail=ans_detail,
                                     session=self._session)
                else:
                    params['offset'] = i * pagesize
                    data['params'] = json.dumps(params)
                    count = 2
                    answer_list = []
                    while(count):
                        try:
                            r = self._session.post(Question_Get_More_Answer_URL,
                                                   data=data,
                                                   headers=new_header)
                            answer_list = r.json()['msg']
                            break
                        except Exception as e:
                            count = count - 1
                            if not count:
                                logger.info('exception ocurred in zhihu_question at answer, question url is:' + self._url)
                                logger.error(str(e))
                                break
                            logger.info('sleep in zhihu_question at answers, question url is:' + self._url)
                            time.sleep(2)

                    if count == 0:
                        logger.error('exception occured in zhihu_question at answers, question url is:' + self._url)
                        logger.error('offset:' + (str(i*pagesize)))
                        continue
                    else:
                        for answer_html in answer_list:
                            try:
                                yield self._parse_answer_html(answer_html)
                            except Exception as e:
                                logger.info('exception ocurred in zhihu_question at answers, question url is:' + self._url)
                                logger.error(str(e))
                                continue

    @property
    def top_answer(self):
        """获取排名第一的答案.

        :return: 排名第一的答案
        :rtype: Answer
        """
        for a in self.answers:
            return a

    def top_i_answer(self, i):
        """获取排名某一位的答案.

        :param int i: 要获取的答案的排名
        :return: 答案对象，能直接获取的属性参见answers方法
        :rtype: Answer
        """
        for j, a in enumerate(self.answers):
            if j == i - 1:
                return a

    def top_i_answers(self, i):
        """获取排名在前几位的答案.

        :param int i: 获取前几个
        :return: 答案对象，返回生成器
        :rtype: Answer.Iterable
        """
        for j, a in enumerate(self.answers):
            if j <= i - 1:
                yield a
            else:
                return

    @property
    @check_soup('_author')
    def author(self):
        """获取问题的提问者.
        
        :return: 提问者
        :rtype: Author or zhihu.ANONYMOUS
        """
        from zhihu_author import Zhihu_author, ANONYMOUS

        logs = self._query_logs()
        author_a = logs[-1].find_all('div')[0].a
        if author_a.text == '匿名用户':
            return ANONYMOUS
        else:
            url = Zhihu_URL + author_a['href']
            return Zhihu_author(url, name=author_a.text, session=self._session)

    @property
    @check_soup('_creation_time')
    def creation_time(self):
        """
        :return: 问题创建时间
        :rtype: datetime.datetime
        """
        logs = self._query_logs()
        time_string = logs[-1].find('div', class_='zm-item-meta').time[
            'datetime']
        return datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")

    @property
    @check_soup('_last_edit_time')
    def last_edit_time(self):
        """
        :return: 问题最后编辑时间
        :rtype: int
        """
        count = 2
        while(count):
            try:
                data = {'_xsrf': self.xsrf, 'offset': '1'}
                res = self._session.post(self.url + 'log', data=data)
                _, content = res.json()['msg']
                soup = BeautifulSoup(content)
                time_string = soup.find_all('time')[0]['datetime']
                #return datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")
                timeArray = time.strptime(time_string, "%Y-%m-%d %H:%M:%S")
                return int(time.mktime(timeArray))
            except Exception as e:
                count = count - 1
                if not count:
                    logger.info('exception ocurred in zhihu_question at last_edit_time, question url is:' + self._url)
                    logger.error(str(e))
                    return 0
                logger.info('sleep in zhihu_question at last_edit_time, question url is:' + self._url)
                time.sleep(1)
                continue

    def _query_logs(self):
        if self._logs is None:
            gotten_feed_num = 20
            start = '0'
            offset = 0
            api_url = self.url + 'log'
            logs = None
            while gotten_feed_num == 20:
                data = {'_xsrf': self.xsrf, 'offset': offset, 'start': start}
                res = self._session.post(api_url, data=data)
                gotten_feed_num, content = res.json()['msg']
                offset += gotten_feed_num
                soup = BeautifulSoup(content)
                logs = soup.find_all('div', class_='zm-item')
                start = logs[-1]['id'][8:] if len(logs) > 0 else '0'
                time.sleep(0.2)  # prevent from posting too quickly

            self._logs = logs

        return self._logs

    # noinspection PyAttributeOutsideInit
    def refresh(self):
        """刷新 Question object 的属性. 
        例如回答数增加了, 先调用 ``refresh()`` 
        再访问 answer_num 属性, 可获得更新后的答案数量.
        
        :return: None
        """
        super().refresh()
        self._html = None
        self._title = None
        self._details = None
        self._answer_num = None
        self._follower_num = None
        self._topics = None
        self._last_edit_time = None
        self._logs = None

    @property
    @check_soup('_deleted')
    def deleted(self):
        """问题是否被删除, 被删除了返回 True, 未被删除返回 False
        :return: True or False
        """
        return self._deleted

    def _parse_answer_html(self, answer_html):
        from zhihu_author import Zhihu_author
        from zhihu_answer import Zhihu_answer
        soup = BeautifulSoup(answer_html)
        # 修正各种建议修改的回答……
        error_answers = soup.find_all('div', id='answer-status')

        for each in error_answers:
            each['class'] = 'zm-editable-content'

        answer_url = self.url + 'answer/' + soup.div['data-atoken']
        #author = soup.find('div', class_='zm-item-answer-author-info')
        up_num = int(soup.find(
            'div', class_='zm-item-vote-info')['data-votecount'])
        #content = soup.find('div', class_='zm-editable-content')
        #content = answer_content_process(content)
        ans_detail = soup.find('div', class_='zm-editable-content').text.replace('\n', '')
        
        com_num = soup.find('a', class_='toggle-comment')
        s = com_num.text
        m = re.findall(r'(\w*[0-9]+)\w*',s)
        if m:
            com_num = int(m[0])
        else:
            com_num = 0
            
        cre_time = soup.find('a', class_='answer-date-link')
        s = cre_time.text
        results = re.search(r'\d{4}-\d{2}-\d{2}', s)
        if results:
            cre_time = results.group(0)
            timeArray = time.strptime(cre_time, "%Y-%m-%d")
            cre_time = int(time.mktime(timeArray))
        else:
            cre_time = 0
        
        author_info = soup.find('div', class_='zm-item-answer-author-info')
        badge = 0
        if author_info.find('span', class_='icon icon-badge-identity icon-badge'):
            badge = 1
        elif author_info.find('span', class_='icon icon-badge-best_answerer'):
            badge = 2
        elif author_info.find('span', class_='icon icon-badge-id-an icon-badge'):
            badge = 3
        #a_url, name, motto, photo = parser_author_from_tag(author)
        #author = Zhihu_author(a_url, name, motto, photo_url=photo,
        #                session=self._session)
        return Zhihu_answer(answer_url, self, author_badge=badge, upvote_num=up_num, comment_num=com_num, creation_time=cre_time, detail=ans_detail,
                      session=self._session)
