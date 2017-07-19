#!/usr/bin/env python3
# -*- coding: utf-8 -*-      
import zhihu_client
import time
import json
import logging
import logging.config

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("zhihu_crawler.py")

def main():
   zhihu_cookie = 'zhihu_cookie.json'
   client = zhihu_client.ZhihuClient(zhihu_cookie)
   topic_list = []
   topic = client.zhihu_topic("https://www.zhihu.com/topic/19550757")
   topic_list.append(topic)
   subTopics = topic.children
   ##topic_list.append(subTopics)
   topic_id_set = set()
   i = 0
   for sub in subTopics:
      topic_list.append(sub)
   for question in topic_list:
      i += 1
      print(str(i)+'---id:'+str(question.id))

if __name__ == '__main__':
    main() 
