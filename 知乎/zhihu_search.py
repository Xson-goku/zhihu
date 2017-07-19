from bs4 import BeautifulSoup 
import json
import re
from zhihu_common import *

class Zhihu_search():
    def __init__(self, keywords, session):
        self._keywords = keywords
        self._session = session

    def search(self):
        step = 10
        search_offset = 0
        url = 'https://www.zhihu.com/r/search?q=keywords&type=content&offset=search_offset'
        question_set = set()
        article_set = set()
        while True:
            search_url = url.replace('keywords', self._keywords).replace('search_offset', str(search_offset))
            res = self._session.get(search_url)            
            res_dict = json.loads(res.text)
            li_list = res_dict['htmls']
            if not li_list:
                result_dict = {"questions":question_set, "articles":article_set}
                return result_dict
            for li in li_list:
                soup = BeautifulSoup(li)
                li_element = soup.find_all('li', class_='item clearfix')
                if li_element and (self._keywords in li_element[0].div.a.text):
                    #pattern = re.compile("/question\/(\d+)")
                    #question_id = pattern.search(li_element[0].div.a['href']).group(1)
                    question_set.add(Zhihu_URL + li_element[0].div.a['href'])
                li_element = soup.find_all('li', class_='item clearfix article-item')
                
                if li_element and (self._keywords in li_element[0].div.a.text):                    
                    #pattern = re.compile(".*/p\/(\d+)")
                    #article_id = pattern.search(li_element[0].div.a['href']).group(1)
                    article_set.add(li_element[0].div.a['href'])  
   
            search_offset += step

            