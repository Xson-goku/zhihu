#!/usr/bin/env python3
# -*- coding: utf-8 -*-      
import zhihu_client
import time
import datetime
import json
import redis_db
import logging
import logging.config

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("questions_crawler.py")


def getCrawlDate(num): 
    today=datetime.date.today() 
    delta=datetime.timedelta(days=num) 
    crawlDate=today-delta  
    return str(crawlDate)

def main():
    zhihu_cookie = 'zhihu_cookie.json'
    client = zhihu_client.ZhihuClient(zhihu_cookie)
    crawl_date = getCrawlDate(1)
    while True:
        task,brand_id,task_type= redis_db.TopicTasks.fetch_task()
        if task:
            if task_type == 1:
                topic = client.zhihu_topic("https://www.zhihu.com/topic/"+str(task))
                questions = topic.questions
                for question in questions:
                    print('---id:'+str(question.id))
                    redis_db.Questions.store_question(brand_id, question.id,crawl_date)

if __name__ == '__main__':
    main() 
