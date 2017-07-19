# -*- coding: utf-8 -*-
import pymysql
import time
import json
import requests
import redis_db
import datetime
import zhihu_client

def getCrawlDate(num): 
    today=datetime.date.today() 
    delta=datetime.timedelta(days=num) 
    crawlDate=today-delta  
    return str(crawlDate)

def get_topic_ids(id):
   zhihu_cookie = 'zhihu_cookie.json'
   client = zhihu_client.ZhihuClient(zhihu_cookie)
   topic_list = []
   topic = client.zhihu_topic("https://www.zhihu.com/topic/"+str(id))
   topic_list.append(topic)
   subTopics = topic.children
   for sub in subTopics:
      topic_list.append(sub)
   return topic_list
if __name__ == '__main__':
   
  print("init zhihu_crawler at:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()))))
  
  #####将当日未搜索的所有话题任务
  redis_db.TopicTasks.move_tasks()
  print('昨日未搜索的所有品牌话题任务已放入未完成set中')
  #####将当日未搜索的所有微博mid放入历史set中
  redis_db.Questions.move_questions()
  print('昨日未搜索回答的问题url已放入历史set中')
  
  ##获取需要抓取的关键词
  conn = pymysql.connect('localhost','own', 'Gx2!@dssfde$$$11', 'weibo_db', charset="utf8")
  cur = conn.cursor()
  
  sql = "select id,name,zhihu_topic_id from brand"
  cur.execute(sql)
  rows = cur.fetchall()  
  cur.close()
  conn.close()
  for row in rows:
    brand_id = row[0]
    brand_name = row[1]
    zhihu_topic_id = row[2]
    if zhihu_topic_id:
       redis_db.TopicTasks.store_task(brand_id,zhihu_topic_id,1)
    else:
       redis_db.TopicTasks.store_task(brand_id,brand_name,2)
  print("crawler-init finished at:" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()))))
