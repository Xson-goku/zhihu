# coding:utf-8
import datetime
import json
import redis
import time
from config.conf import get_redis_args

redis_args = get_redis_args()


class TopicTasks(object):
    rd_con = redis.StrictRedis(host=redis_args.get('host'), port=redis_args.get('port'),
                               password=redis_args.get('password'), db=redis_args.get('cookies'))

    rd_con_broker = redis.StrictRedis(host=redis_args.get('host'), port=redis_args.get('port'),
                                      password=redis_args.get('password'), db=redis_args.get('broker'))
    @classmethod
    def store_task(cls, brand_id, task,task_type):
        picked_task = json.dumps(
            {'brand_id': brand_id,'task':task,'task_type':task_type})
        cls.rd_con.sadd('zhihu:set:topic', picked_task)
    @classmethod
    def fetch_task(cls):
        topic_json = cls.rd_con.spop('zhihu:set:topic')
        if topic_json is None :
            return None,None,None
        task = json.loads(topic_json.decode())['task']
        brand_id = json.loads(topic_json.decode())['brand_id']
        task_type = json.loads(topic_json.decode())['task_type']
        return task,brand_id,task_type
	#####将当日未搜索的所有问题插入到未爬取set中
    @classmethod
    def move_tasks(cls):
        num = cls.rd_con.scard('zhihu:set:topic')
        i = 0 
        while i < num:
            task_json = cls.rd_con.spop('zhihu:set:topic')
            cls.rd_con.sadd('zhihu:set:topic:unsearch',task_json)
            i=i+1
   	#####将当日未搜索的所有关键词插入到历史set中
    @classmethod
    def scard(cls,setname):
        num = cls.rd_con.scard(setname)
        return num  


class Questions(object):
    rd_con = redis.StrictRedis(host=redis_args.get('host'), port=redis_args.get('port'),
                               password=redis_args.get('password'), db=redis_args.get('urls'))
    ###存储问题id和brand_id
    @classmethod
    def store_question(cls, brand_id, question_id,crawl_date):
        picked_question = json.dumps(
            {'brand_id': brand_id, 'question_id': question_id})
        i = cls.rd_con.sadd('zhihu:set:questions'+crawl_date, picked_question)
        print('-----i:'+str(i)+',mid:'+str(question_id))
        if i > 0:
            cls.rd_con.sadd('zhihu:set:questions', picked_question)
	###获取一个问题id
    @classmethod
    def fetch_question(cls,set_name):
        question_json = cls.rd_con.spop(set_name)
        max_try_num = 3
        ###如果获取不到问题id，尝试三次，每次间隔10分钟
        while question_json is None and max_try_num >0:
            max_try_num = max_try_num -1
            time.sleep(600)
            question_json = cls.rd_con.spop(set_name)
        if question_json is None :
            print('----问题id已空，请尽快确认爬虫任务是否完成')
            return None,None
        question_id = json.loads(question_json.decode())['question_id']
        brand_id = json.loads(question_json.decode())['brand_id']
        return brand_id,question_id
	#####将当日未搜索的所有问题插入到未爬取set中
    @classmethod
    def move_questions(cls):
        num = cls.rd_con.scard('zhihu:set:questions')
        i = 0 
        while i < num:
            question_json = cls.rd_con.spop('zhihu:set:questions')
            cls.rd_con.sadd('zhihu:set:questions:unsearch',question_json)
            i=i+1
   	#####将当日未搜索的所有关键词插入到历史set中
    @classmethod
    def scard(cls,setname):
        num = cls.rd_con.scard(setname)
        return num

def main():
    cd = Questions()
    cd.move_questions()
if __name__ == '__main__':
    main()
