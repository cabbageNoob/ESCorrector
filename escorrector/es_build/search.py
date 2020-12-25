'''
Descripttion: 
Author: cjh (492795090@qq.com)
Date: 2020-12-04 18:18:41
'''
import json, time
from elasticsearch import Elasticsearch
es = Elasticsearch()

def filter_msg(msg,index_name=''):
    body = {
        "size": 10,
        "query": {
            "match": {
                "sentence":msg
            }
        }
    }
    res = es.search(index=index_name, body=body)
    return json.dumps((res['hits']['hits']), indent=4, ensure_ascii=False)
    # return res['hits']['hits']

def filter_phrase_msg(msg,index_name=''):
    body = {
        "size": 10,
        "query": {
            "match_phrase": {
                "sentence":msg
            }
        }
    }
    res = es.search(index=index_name, body=body)
    return json.dumps((res['hits']['hits']), indent=4, ensure_ascii=False)


if __name__ == '__main__':
    t1=time.time()
    # print(filter_msg('你好'))
    # print(time.time() - t1)
    print(filter_phrase_msg('云在',index_name='corpus'))
    print(time.time() - t1)