# coding: utf-8

__version__ = '1.1.0'
__author__ = 'chenmin (1019717007@qq.com)'

'''
以关键词收集新浪微博
'''
import json
import time
import datetime
import random
import logging
import sys
import redis_db
from zhihu_common import *
import pymongo
import requests
import os
import common_utils

class CollectData():
    """单条微博及用户信息收集类

        大体思路：利用微博API获取单条微博内容、评论数、点赞数、转发数、第一页评论、作者信息等内容

        单条微博内容获取地址：https://m.weibo.cn/status/4110221791827771

        第一页评论数据获取地址：https://m.weibo.cn/api/comments/show?id=4078996901408644&page=1
    """
    def __init__(self, brand_id,question_id,collection,crawl_date,answer_url_start="https://www.zhihu.com/api/v4/questions/",
                 answer_url_end="/answers?include=data[*].is_normal%2Cis_collapsed%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata[*].author.follower_count%2Cbadge[%3F(type%3Dbest_answerer)].topics&limit=20&offset=0&sort_by=default" ):
        self.answer_url_start = answer_url_start  #设置固定地址起始部分
        self.question_id = question_id
        self.collection = collection
        self.answer_url_end = answer_url_end
        self.crawl_date= crawl_date #设置爬虫日期
        self.brand_id = brand_id
        self.logger = logging.getLogger('main.CollectData') #初始化日志
    ##构建第一页回答url
    def getAnswersURL(self):
        return self.answer_url_start+ str(self.question_id)+self.answer_url_end
    
    def getCookies(self):
        cookies_dict = {}
        cookies_file = 'zhihu_cookie.json'
        if os.path.isfile(cookies_file):
            with open(cookies_file) as f:
                cookies = f.read()
        cookies_dict = json.loads(cookies)
        return cookies_dict

    ##爬取具体数据
    def download(self,url,maxTryNum=4):
        print('-----url: '+url)
        cookies = self.getCookies()
        for tryNum in range(maxTryNum):
            try:
                resp = requests.get(url, headers=Default_Header, cookies=cookies,timeout=3)
                break
            except:
                if tryNum < (maxTryNum-1):
                    time.sleep(10)
                else:
                    print('Internet Connect Error!')
                    ###########增加短信验证码
                    resp = None
                    hostname = common_utils.get_hostname()
                    message_content = 'url:'+url+',zhihu Connect Error,hostname:'+hostname
                    common_utils.send_messag("18561906132",message_content)
                    return
        try:
            response_data = resp.json()
            is_end = False
            next_url = None
            if response_data:
                is_end = response_data['paging']['is_end']
                print(is_end)
                next_url = response_data['paging']['next']
                answer_list = response_data['data']
                for answer in answer_list:
                    answer_dict = {}
                    answer_dict['answer_data'] = answer
                    answer_dict['brand_id']=self.brand_id
                    answer_dict['crawl_date']=self.crawl_date
                    self.collection.insert(answer_dict)
        except:
            print('return result has been changed!')
            ###########增加短信验证码
            resp = None
            is_end = True
            self.logger.info('question_id:'+str(self.question_id)+',resp:'+str(resp))
            hostname = common_utils.get_hostname()
            message_content = 'url:'+url+',zhihu return changed,hostname:'+hostname
            common_utils.send_messag("18561906132",message_content)
            return is_end,None
        return is_end,next_url

####获取需要爬取的日期
def getCrawlDate(num): 
    today=datetime.date.today() 
    delta=datetime.timedelta(days=num) 
    crawlDate=today-delta  
    return str(crawlDate)


def main():
    logger = logging.getLogger('main')
    logFile = './run_collect.log'
    logger.setLevel(logging.DEBUG)
    filehandler = logging.FileHandler(logFile)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    client = pymongo.MongoClient("139.129.222.132", 27017)
    db=client['zhihu_db']
    collection=db['answer']
    crawlDate = getCrawlDate(1)
    while True:
        #####获取问题id
        brand_id,question_id= redis_db.Questions.fetch_question("zhihu:set:questions")
        if not question_id:
           print('task is over!')
           return
        cd = CollectData(brand_id,question_id,collection,crawlDate)
        is_end = False
        next_url = cd.getAnswersURL()
        while not is_end:
            is_end,next_url = cd.download(next_url)
            time.sleep(random.randint(5,15))
        time.sleep(random.randint(5,15))
    else:
        logger.removeHandler(filehandler)
        logger = None
if __name__ == '__main__':
    main()
